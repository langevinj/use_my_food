const SEARCH_BY_ING_URL = "https://api.spoonacular.com/recipes/findByIngredients?ingredients="
const BASE_URL = "http://127.0.0.1:5000"

//Click handler for searching by ingredient
$('#search-for-recipes').click(async function (evt) {
    evt.preventDefault();

    //grab all search ingredients and the number of desired recipes to return
    let ingredients = $('#searchIngredients').val();
    let val = $('input[type="radio"][name="optradio"]:checked').val()
    let numRecipes = parseInt(val)

    //remove any previous errors
    $('#emptyError').empty()
    
    //create an error if ingredient field is empty
    if (ingredients === ""){
        let emptyError = "<p class='text-danger' id='emptyError'>Please enter at least 1 ingredient</p>"
        $(`#emptyError`).append(emptyError)
        return 
    }

    //Prepare a list of ingredients for the query string
    let ingArray = separateIngredients(ingredients);
    let ingStr = ingArray.join(",+")

    let res = await axios.post(`${BASE_URL}/ingredient-search`, json={"number": numRecipes, "ingStr": ingStr})
    let recipeInfo = await getRecipeInfo(res.data['data'])
    listRecipes(recipeInfo)
})

//Separate comma-separated ingredients and return an array of each
function separateIngredients(ingredients){

    let loweredIng = ingredients.toLowerCase()
    let array = loweredIng.split(", ")
    return array
}

//Get extended recipe information from the API, based on the number of recipes desired
async function getRecipeInfo(recipes){
    let allIds = []
    let x = recipes.length

    for(let i=0; i < x; i++){
        let id = recipes[i].id
        allIds.push(id)
    }
    
    let info;
    //Will not need unless searching for 1 recipe is enabled
    // if (allIds.length == 1){
    //     // info = await axios.get(`https://api.spoonacular.com/recipes/${allIds[0]}/information?apiKey=${config["apiKey"]}`)

    let ids = allIds.join(",")
    info = await axios.post(`${BASE_URL}/ingredient-search-recipes-helper`, json={'ids': ids})
        
    return info.data['data']
}

//Distill only the data required from the response from the API, and clean up each recipe
function listRecipes(recipes) {
    $('#recipeList').empty()
    let x = recipes.length;

    if(x > 1 && x != undefined){
        for(let i=0; i < x; i++){
            let id = recipes[i].id
            let title = recipes[i].title
            let image = recipes[i].image
            let sourceUrl = recipes[i].sourceUrl
            let vegetarian = recipes[i].vegetarian
            let vegan = recipes[i].vegan
            appendRecipe(id, title, image, sourceUrl, vegetarian, vegan)
        }
    } else {
        let id = recipes.id
        let title = recipes.title
        let image = recipes.image
        let sourceUrl = recipes.sourceUrl
        let vegetarian = recipes.vegetarian
        let vegan = recipes.vegan
        appendRecipe(id, title, image, sourceUrl, vegetarian, vegan)
    }
    toggle_favorite_icons()
    toggle_view_rating()
}

//Appends a recipe to the page
function appendRecipe(id, title, image, sourceUrl, isVegetarian, isVegan){
    let $recipeList = $('#recipeList')

    let tempRecipeHTML = `<li id="${id}"><a class="title" href=${sourceUrl} target="_blank">${title}</a><span class="vegetarian hidden">Vegetarian</span><span class="vegan hidden">Vegan</span><button class="favoriteButton"></button><span><form action="/ratings/rate" method="GET" id="ratingForm"><input class="hidden" value="${id}" type="number" name="api_id"><button>Rate this recipe</button></form></span><span><form class="viewRatingForm" action='/ratings'></form></span><br><div class="recipeImage row justify-content-center"><img src=${image} alt="${title}" class="foodImg"></div></li><br>`

    $recipeList.append(tempRecipeHTML)

    //makes Vegetarian or Vegan distincitions visible
    if(isVegetarian){
        $(`#${id} .vegetarian`).removeClass("hidden")
    }

    if (isVegan){
        $(`#${id} .vegan`).removeClass("hidden")
    }
}

 //toggle a favorite when clicked, save the favorite to the recipe DB if not already present
$('body').on("click", ".favoriteButton", async function(evt){
    evt.preventDefault();

    //grab all recipe information from the page
    let api_id = evt.target.parentNode.id
    let clicked_button = $(`#${api_id} > .favoriteButton`)
    let image_url = clicked_button.siblings('.recipeImage').find('img').attr('src')
    let recipe_url = $(`#${api_id} .title`).prop('href')
    let name = $(`#${api_id} .title`).text()
    let vegetarian = !$(`#${api_id} .vegetarian`).hasClass('hidden')
    let vegan = !$(`#${api_id} .vegan`).hasClass('hidden')

    //add the recipe to the recipe table, get back recipe.id 
    let res = await axios.post(`${BASE_URL}/add_recipe`, {"recipe_id": api_id, "image_url": image_url, "name": name, "recipe_url": recipe_url, "vegetarian": vegetarian, "vegan": vegan})
    let id;

    //Determine if the user's view is on the favorite's page
    let onFavoritesPage = clicked_button.hasClass('favoritePage')

    if(res){
        id = res.data['id'];
    }
    
    //toggle a favorite between favorited and not
    let toggled = await axios.post(`${BASE_URL}/users/toggle_favorite`, {"id": id})

    //switch the favorite button when clicking, if on the favorites page, remove from the DOM
    if(toggled.data == "unfavorited"){
        clicked_button.empty()
        clicked_button.append('<i class="far fa-star"></i>')
        if(onFavoritesPage){
            $(`#${api_id}`).remove()
        }
    } else {
        clicked_button.empty()
        clicked_button.append('<i class="fas fa-star"></i>')
    }
})

//When a page loads, toggle the favorite buttons filled in or not
async function toggle_favorite_icons(){
    check_loggedin = $('*:contains("Login")')
    if (check_loggedin){
        return
    }

    //Get a list of all the api_ids of the current user's favorites
    let data = await axios.get(`${BASE_URL}/users/curruser/favorites`)
    let all_fav_recipe_ids = Object.entries(data.data['favIds'])

    let fav_arr = create_fav_arr(all_fav_recipe_ids)
    let all_fav_buttons = Array.from(document.getElementsByClassName('favoriteButton'))

    //Iterate through all the favorite buttons, changing the icon displayed according to if the recipe is present in the fav_arr
    for(let y=0; y<all_fav_buttons.length;y++){
        let fav_button = all_fav_buttons[y]
        let id = fav_button.parentNode.id
        //fill in favorite icons if they exist for the user
        if(fav_arr.includes(id)){
            $(`#${id} > .favoriteButton`).append('<i class="fas fa-star"></i>')
        } else {
            $(`#${id} > .favoriteButton`).append('<i class="far fa-star"></i>')
        }
    }
}   

//Clean up the string data of all favorites to just api_ids
function create_fav_arr(all_fav_recipe_ids) {
    let raw_arr = []
    for (let i = 0; i < all_fav_recipe_ids.length; i++) {
        raw_arr.push(all_fav_recipe_ids[i][1])
    }

    let str = JSON.stringify(raw_arr)
    let str2 = str.slice(0, -1)
    str2 = str2.substring(1)
    let str_arr = str2.split(",")
    let fav_arr = []
    for (let x = 0; x < str_arr.length; x++) {
        fav_arr.push(str_arr[x])
    }
    return fav_arr
}

//If a recipe has any ratings in the DB, display the button that allows a user to view its ratings
async function toggle_view_rating() {
    let data = await axios.get(`${BASE_URL}/ratings/all_recipe_ids`)
    let all_rated_ids = (data.data['ids'])

    let all_view_ratings_buttons = Array.from(document.getElementsByClassName('viewRatingForm'))

    //Iterate through all recipes and add "view ratings" button
    for(let i=0; i<all_view_ratings_buttons.length;i++){
        let button = all_view_ratings_buttons[i]
        let id = button.parentNode.parentNode.id
        if(all_rated_ids.includes(parseInt(id))){
            $(`#${id} > .viewRatingForm`).append(`<button name='api_id' value=${id}>View ratings</button>`)
        }
    }
}

//Event listener for the submission of the converter
$('#convertButton').click(async function(evt){
    evt.preventDefault()
    let sourceIngredient = $('#sourceIngredient').val()
    let sourceAmount = $('#sourceAmount').val()
    let sourceUnit = $('#sourceUnit').val()
    let targetUnit = $('#targetUnit').val()

    //handle an invalid amount input
    if(!parseFloat(sourceAmount)){
        $('#converterError').text('')
        $('#converterError').text('Not a valid amount')
        return
    } else if (sourceUnit == targetUnit){
        $('#convertedAmount').val(sourceAmount)
    } else {

        let converted = await axios.post(`${BASE_URL}/converter-helper`, json={"sourceIngredient": sourceIngredient, "sourceAmount": sourceAmount, "sourceUnit": sourceUnit, "targetUnit": targetUnit})

        let targetAmount = converted.data['data']['targetAmount']
        $('#convertedAmount').val(targetAmount)
    }
})

//If a user has rated a recipe, hide the "Rate this Recipe" button and allow the user to edit their previous rating
function toggle_all_edit_rating_buttons(){
    let recipes_list = Array.from(document.getElementById('content').querySelectorAll('li'))

    for(let i=0; i < recipes_list.length; i++){
        let id = recipes_list[i].id
        let rate = $(`#${id} > .rateButton`)
        let check = $(`#${id} > .editRatingForm`)
        if (check.length > 0){
            rate.hide()
        }
    }
}


//On loading of page always toggle favorites and if the user can edit their rating for recipes
window.onload = toggle_favorite_icons()
window.onload = toggle_all_edit_rating_buttons()

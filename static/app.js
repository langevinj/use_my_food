const SEARCH_BY_ING_URL = "https://api.spoonacular.com/recipes/findByIngredients?ingredients="

const BASE_URL = "http://127.0.0.1:5000"

$('#search-for-recipes').click(function(evt){
    evt.preventDefault()
    let rad = $('input[type="radio"][name="optradio"]:checked').val()
    let val = parseInt(rad)
})


$('#search-for-recipes').click(async function (evt) {
    evt.preventDefault();
    //remove any previos error from leaving the field empty
    $('#emptyError').remove()

    //grab all search ingredients and number of desired recipes to return
    let ingredients = $('#searchIngredients').val();
    let val = $('input[type="radio"][name="optradio"]:checked').val()
    let numRecipes = parseInt(val)
    
    //create error if ingredient field is empty
    if (ingredients == ""){
        let emptyError = "<p class='text-danger' id='emptyError'>Please enter at least 1 ingredient</p>"
        $(`${emptyError}`).insertBefore('.dropdown')
        return 
    }

    let ingArray = separateIngredients(ingredients);
    let ingStr = ingArray.join(",+")

    //get recipes based on input ingredients
    let res = await axios.get(`${SEARCH_BY_ING_URL}${ingStr}&number=${numRecipes}&apiKey=${config["apiKey"]}`)
    let recipeInfo = await getRecipeInfo(res)
    listRecipes(recipeInfo)
})

function separateIngredients(ingredients){
//Return an array of all ingredients entered
    let loweredIng = ingredients.toLowerCase()
    let array = loweredIng.split(", ")
    return array
}


//gets extended information on all recipes passed in as 1 object
async function getRecipeInfo(recipes){
    let allIds = []
    let x = recipes.data.length

    for(let i=0; i < x; i++){
        let id = recipes.data[i].id
        allIds.push(id)
    }
    
    let info;
    if (allIds.length == 1){
        info = await axios.get(`https://api.spoonacular.com/recipes/${allIds[0]}/information?apiKey=${config["apiKey"]}`)
    } else {
        let ids = allIds.join(",")
        info = await axios.get(`https://api.spoonacular.com/recipes/informationBulk?ids=${ids}&apiKey=${config["apiKey"]}`)
    }
    return info
}

//grab recipe info and append the list to the page
function listRecipes(recipes) {
    $('#recipeList').empty()
    let x = recipes.data.length;

    if(x > 1 && x != undefined){
        for(let i=0; i < x; i++){
            let id = recipes.data[i].id
            let title = recipes.data[i].title
            let image = recipes.data[i].image
            let sourceUrl = recipes.data[i].sourceUrl
            let vegetarian = recipes.data[i].vegetarian
            let vegan = recipes.data[i].vegan
            appendRecipe(id, title, image, sourceUrl, vegetarian, vegan)
        }
    } else {
        let id = recipes.data.id
        let title = recipes.data.title
        let image = recipes.data.image
        let sourceUrl = recipes.data.sourceUrl
        let vegetarian = recipes.data.vegetarian
        let vegan = recipes.data.vegan
        appendRecipe(id, title, image, sourceUrl, vegetarian, vegan)
    }
    toggle_favorite_icons()
    toggle_view_rating()
}

//appends recipes to list
function appendRecipe(id, title, image, sourceUrl, isVegetarian, isVegan){
    let $recipeList = $('#recipeList')

    let tempRecipeHTML = `<li id="${id}"><a class="title" href=${sourceUrl} target="_blank">${title}</a><span class="vegetarian hidden">Vegetarian</span><span class="vegan hidden">Vegan</span><button class="favoriteButton"></button><span><form action="/ratings/rate" method="GET"><input class="hidden" value="${id}" type="number" name="api_id"><button class="rateRecipe">Rate this recipe</button></form></span><span><form class="viewRatingForm" action='/ratings'></form></span><br><img src=${image}></li>`

    $recipeList.append(tempRecipeHTML)

    if(isVegetarian){
        $(`#${id} .vegetarian`).removeClass("hidden")
    }

    if (isVegan){
        $(`#${id} .vegan`).removeClass("hidden")
    }
}

 //toggle a favorite when clicked, save the favorite if not already present
$('body').on("click", ".favoriteButton", async function(evt){
    evt.preventDefault();
    console.log("clicked")
    let api_id = evt.target.parentNode.id
    let clicked_button = $(`#${api_id} > .favoriteButton`)
    let image_url = clicked_button.siblings('img').attr('src')
    let recipe_url = $(`#${api_id} .title`).prop('href')
    let name = $(`#${api_id} .title`).text()
    let vegetarian = !$(`#${api_id} .vegetarian`).hasClass('hidden')
    let vegan = !$(`#${api_id} .vegan`).hasClass('hidden')

    //add the recipe to the recipe table, get back recipe.id 
    let res = await axios.post(`${BASE_URL}/add_recipe`, {"recipe_id": api_id, "image_url": image_url, "name": name, "recipe_url": recipe_url, "vegetarian": vegetarian, "vegan": vegan})
    let id;

    console.log(res)

    let onFavoritesPage = clicked_button.hasClass('favoritePage')
    console.log(onFavoritesPage)
    if(res){
        id = res.data['id'];
    }
    
    let toggled = await axios.post(`${BASE_URL}/users/toggle_favorite`, {"id": id})
    console.log(toggled)

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

//This definitely needs to be simplified
async function toggle_favorite_icons(){
    //Get a list of all the api_ids of the current user's favorites
    let data = await axios.get(`${BASE_URL}/users/curruser/favorites`)
    let all_fav_recipe_ids = Object.entries(data.data['favIds'])

    let fav_arr = create_fav_arr(all_fav_recipe_ids)
    let all_fav_buttons = Array.from(document.getElementsByClassName('favoriteButton'))

    //Iterate through all the favorite buttons, changing the icon displayed according to if the recipe is present in the fav_arr
    for(let y=0; y<all_fav_buttons.length;y++){
        let fav_button = all_fav_buttons[y]
        let id = fav_button.parentNode.id
        if(fav_arr.includes(id)){
            $(`#${id} > .favoriteButton`).append('<i class="fas fa-star"></i>')
        } else {
            $(`#${id} > .favoriteButton`).append('<i class="far fa-star"></i>')
        }
    }
}   

//function to clean up the string data of all favorites api_ids
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

async function toggle_view_rating() {
    let data = await axios.get(`${BASE_URL}/ratings/all_recipe_ids`)
    let all_rated_ids = (data.data['ids'])

    let all_view_ratings_buttons = Array.from(document.getElementsByClassName('viewRatingForm'))

    //Iterate through all recipes and add "view ratings" button if the recipe has any ratings
    for(let i=0; i<all_view_ratings_buttons.length;i++){
        let button = all_view_ratings_buttons[i]
        let id = button.parentNode.parentNode.id
        if(all_rated_ids.includes(parseInt(id))){
            $(`#${id} > span > .viewRatingForm`).append(`<button class='viewRatingsForm' name='api_id' value=${id}>View this recipe's ratings</button>`)
        }
    }
}



$('#convertButton').click(async function(evt){
    evt.preventDefault()
    let sourceIngredient = $('#sourceIngredient').val()
    let sourceAmount = $('#sourceAmount').val()
    let sourceUnit = $('#sourceUnit').val()
    let targetUnit = $('#targetUnit').val()

    console.log(parseFloat(sourceAmount))

    //handle an invalid amount input
    if(!parseFloat(sourceAmount)){
        $('#converterError').text('')
        $('#converterError').text('Not a valid amount')
        return
    } else if (sourceUnit == targetUnit){
        $('#convertedAmount').val(sourceAmount)
    } else {
        let converted = await axios.get(`https://api.spoonacular.com/recipes/convert?ingredientName=${sourceIngredient}&sourceAmount=${sourceAmount}&sourceUnit=${sourceUnit}&targetUnit=${targetUnit}&apiKey=${config["apiKey"]}`)

        let targetAmount = converted.data['targetAmount']
        $('#convertedAmount').val(targetAmount)
    }

})


//On loading of page always toggle favorites for recipes
window.onload = toggle_favorite_icons()
// window.onload = toggle_view_rating()
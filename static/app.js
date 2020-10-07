const SEARCH_BY_ING_URL = "https://api.spoonacular.com/recipes/findByIngredients?ingredients="

const BASE_URL = "http://127.0.0.1:5000"

// $('#search-for-recipes').click(function(evt){
//     evt.preventDefault()
//     let rad = $('input[type="radio"][name="optradio"]:checked').val()
//     let val = parseInt(rad)
//     let test = $('#searchIngredients').val();
//     console.log(test)
// })


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
}

//appends recipes to list
function appendRecipe(id, title, image, sourceUrl, isVegetarian, isVegan){
    let $recipeList = $('#recipeList')

    let tempRecipeHTML = `<li id="${id}"><a class="title" href=${sourceUrl} target="_blank">${title}</a><span class="vegetarian hidden">Vegetarian</span><span class="vegan hidden">Vegan</span><button class="favoriteButton"></button><br><img src=${image}></li>`

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
    let recipeId = evt.target.parentNode.id
    let clicked_button = $(`#${recipeId} > .favoriteButton`)
    let img_src = clicked_button.siblings('img').attr('src')
    let recipe_url = $(`#${recipeId} .title`).prop('href')
    let name = $(`#${recipeId} .title`).text()

    let res = await axios.post(`${BASE_URL}/users/toggle_favorite/`, {"recipe_id": recipeId, "img_src": img_src, "name": name, "recipe_url": recipe_url})
    
    //switch the favorite button when clicking
    if(res.data == "unfavorited"){
        clicked_button.empty()
        clicked_button.append('<i class="far fa-star"></i>')
    } else {
        clicked_button.empty()
        clicked_button.append('<i class="fas fa-star"></i>')
    }
})

//This definitely needs to be simplified
async function toggle_favorite_icons(){
    let data = await axios.get(`${BASE_URL}/users/curruser/favorites`)
    let all_fav_recipe_ids = Object.entries(data.data['favIds'])

    let raw_arr = []

    for(let i=0; i < all_fav_recipe_ids.length; i++){
        raw_arr.push(all_fav_recipe_ids[i][1])
    }

    let str = JSON.stringify(raw_arr)
    let str2 = str.slice(0, -1)
    str2 = str2.substring(1)
    let str_arr = str2.split(",")
    let fav_arr = []
    for(let x=0; x<str_arr.length;x++){
        fav_arr.push(str_arr[x])
    }
    
    let all_fav_buttons = Array.from(document.getElementsByClassName('favoriteButton'))

    
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

$('#search-by-recipe').on("submit", async function(evt){
    evt.preventDefault()
    searchTerm = $('#search-term').val()
    let res = await axios.get(`https://api.spoonacular.com/recipes/complexSearch?query=${searchTerm}&number=2&addRecipeInformation=true&apiKey=${config["apiKey"]}`)
    let res2 = await axios.post(`${BASE_URL}/search`, {"data": res, "search_term": searchTerm})
    console.log(res2)
    let data = JSON.stringify(res2)
    let data2 = JSON.parse(data)


    console.log(data2.data.search_term)
    let render_page = await axios.get(`${BASE_URL}/search/${data2.data.search_term}`)
    return 
})
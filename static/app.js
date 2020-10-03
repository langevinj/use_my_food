const SEARCH_BY_ING_URL = "https://api.spoonacular.com/recipes/findByIngredients?ingredients="

const BASE_URL = "http://127.0.0.1:5000"


$('#search-by-ingredient').on("submit", async function (evt) {
    evt.preventDefault();

    //remove any previos error from leaving the field empty
    $('#emptyError').remove()

    //grab all search ingredients and number of desired recipes to return
    let ingredients = $('#searchIngredients').val();
    let numRecipes = $('#recipeRadio input[type="radio"]:checked').val();

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
}

//appends recipes to list
function appendRecipe(id, title, image, sourceUrl, isVegetarian, isVegan){
    let $recipeList = $('#recipeList')

    let tempRecipeHTML = `<li id="${id}"><a href=${sourceUrl} target="_blank">${title}</a><span class="vegetarian hidden">Vegetarian</span><span class="vegan hidden">Vegan</span><br><img src=${image}></li>`

    $recipeList.append(tempRecipeHTML)

    if(isVegetarian){
        $(`#${id} .vegetarian`).removeClass("hidden")
    }

    if (isVegan){
        $(`#${id} .vegan`).removeClass("hidden")
    }
}
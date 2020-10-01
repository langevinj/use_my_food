

$('#search-by-ingredient').on("submit", async function (evt) {
    evt.preventDefault();

    //grab all search ingredients, doesn't currently have any validation
    let $searchIngredients = $('#searchIngredients')
    let ingredients = $searchIngredients.val();

    let ingArray = separateIngredients(ingredients);
    
})

function separateIngredients(ingredients){
//Return an array of all ingredients entered
    let loweredIng = ingredients.toLowerCase()
    let array = loweredIng.split(", ")
    return array
}

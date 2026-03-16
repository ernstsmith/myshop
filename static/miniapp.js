let cart = []

function addToCart(id,name,price){

cart.push({
id:id,
name:name,
price:price
})

renderCart()

}

function renderCart(){

const cartDiv=document.getElementById("cart")

cartDiv.innerHTML=""

cart.forEach(item=>{

const el=document.createElement("div")

el.innerHTML=item.name+" - "+item.price+" ₽"

cartDiv.appendChild(el)

})

}

function checkout(){

const order={
items:cart
}

Telegram.WebApp.sendData(JSON.stringify(order))

}
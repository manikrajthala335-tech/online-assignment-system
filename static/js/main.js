document.addEventListener("DOMContentLoaded", function(){
 document.querySelectorAll("[data-confirm]").forEach(function(btn){
  btn.addEventListener("click",function(e){if(!confirm(btn.dataset.confirm))e.preventDefault();});
 });
 document.querySelectorAll(".file-input").forEach(function(input){
  input.addEventListener("change",function(){
   const box=input.closest(".file-box");
   if(box && input.files.length){const n=box.querySelector(".file-name");if(n)n.textContent=input.files[0].name;}
  });
 });
});



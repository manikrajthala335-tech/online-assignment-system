document.addEventListener("DOMContentLoaded", function(){
  // Confirmation dialogues
  document.querySelectorAll("[data-confirm]").forEach(function(btn){
    btn.addEventListener("click",function(e){if(!confirm(btn.dataset.confirm))e.preventDefault();});
  });

  // Dynamic file name display
  document.querySelectorAll(".file-input").forEach(function(input){
    input.addEventListener("change",function(){
      const box=input.closest(".file-box");
      if(box && input.files.length){const n=box.querySelector(".file-name");if(n)n.textContent=input.files[0].name;}
    });
  });

  // Automatically highlight current active sidebar navigation item
  const currentPath = window.location.pathname;
  let matched = false;
  document.querySelectorAll(".sidebar .nav-item").forEach(function(link) {
    const href = link.getAttribute("href");
    if (href && currentPath === href) {
      link.classList.add("active");
      matched = true;
    }
  });

  // Partial match if exact match wasn't found (for nested pages like edit/add)
  if (!matched) {
    document.querySelectorAll(".sidebar .nav-item").forEach(function(link) {
      const href = link.getAttribute("href");
      if (href && href !== '/' && currentPath.startsWith(href)) {
        link.classList.add("active");
      }
    });
  }
});



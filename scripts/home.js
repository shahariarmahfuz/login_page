// Toggle menu function
function toggleMenu() {
    var menu = document.querySelector('.menu');
    menu.classList.toggle('active');
}

// Add a function to search the content of the page
function searchContent() {
    var input, filter, body, txtValue;
    input = document.getElementById('search');
    filter = input.value.toUpperCase();
    body = document.body;
    txtValue = body.textContent || body.innerText;
    if (txtValue.toUpperCase().indexOf(filter) > -1) {
        body.style.display = "";
    } else {
        body.style.display = "none";
    }
}

// Prevent right-click on all images
document.oncontextmenu = function(e) {
  var target = e.target || e.srcElement;
  if (target.tagName == 'IMG') {
    return false;
  }
};

document.onkeydown = function(e) {
  if (e.ctrlKey && 
     (e.keyCode === 67 || 
      e.keyCode === 86 || 
      e.keyCode === 85 || 
      e.keyCode === 117)) {
    return false;
  } else {
    return true;
  }
};

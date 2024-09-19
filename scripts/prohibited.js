document.addEventListener('DOMContentLoaded', function() {
  // ডান ক্লিক নিষিদ্ধ করা
  document.addEventListener('contextmenu', function(e) {
    if (e.target.tagName === 'IMG') {
      e.preventDefault();
    }
  });

  // ড্র্যাগ নিষিদ্ধ করা
  document.addEventListener('dragstart', function(e) {
    if (e.target.tagName === 'IMG') {
      e.preventDefault();
    }
  });

  // কপি নিষিদ্ধ করা
  document.addEventListener('copy', function(e) {
    if (e.target.tagName === 'IMG') {
      e.preventDefault();
    }
  });

  // ছবি যাতে ডাউনলোড করা না যায় তা নিশ্চিত করতে
  document.addEventListener('mousedown', function(e) {
    if (e.target.tagName === 'IMG') {
      e.preventDefault();
    }
  });
});

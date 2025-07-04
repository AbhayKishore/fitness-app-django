// sidebar.js
document.addEventListener('DOMContentLoaded', function() {
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  
  // Load saved state
  const savedState = localStorage.getItem('sidebarExpanded');
  if (savedState === 'true') {
    sidebar.classList.add('expanded');
    if (mainContent) mainContent.classList.add('expanded');
  }

  // Close sidebar when clicking outside on mobile
  if (window.innerWidth <= 576) {
    document.addEventListener('click', function(e) {
      if (!sidebar.contains(e.target) && !e.target.classList.contains('menu-toggle')) {
        sidebar.classList.remove('expanded');
        if (mainContent) mainContent.classList.remove('expanded');
        localStorage.setItem('sidebarExpanded', 'false');
      }
    });
  }
});

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  
  sidebar.classList.toggle('expanded');
  if (mainContent) mainContent.classList.toggle('expanded');
  
  // Save state
  const isExpanded = sidebar.classList.contains('expanded');
  localStorage.setItem('sidebarExpanded', isExpanded);
  
  // Ensure last item is visible
  if (isExpanded) {
    setTimeout(() => {
      const lastItem = sidebar.querySelector('.sidebar-item:last-child');
      lastItem.scrollIntoViewIfNeeded();
    }, 300);
  }
}
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  
  sidebar.classList.toggle('expanded');
  if (mainContent) mainContent.classList.toggle('expanded');
  
  // Save state
  const isExpanded = sidebar.classList.contains('expanded');
  localStorage.setItem('sidebarExpanded', isExpanded);
}

document.addEventListener('DOMContentLoaded', function() {
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  
  // Load saved state
  const savedState = localStorage.getItem('sidebarExpanded');
  if (savedState === 'true') {
    sidebar.classList.add('expanded');
    if (mainContent) mainContent.classList.add('expanded');
  }

  // Set active item based on current page
  const currentPath = window.location.pathname;
  const menuItems = document.querySelectorAll('.sidebar-item');
  menuItems.forEach(item => {
    if (item.getAttribute('href') === currentPath) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Close sidebar when clicking outside on mobile
  if (window.innerWidth <= 576) {
    document.addEventListener('click', function(e) {
      if (!sidebar.contains(e.target) && !e.target.classList.contains('menu-toggle')) {
        sidebar.classList.remove('expanded');
        if (mainContent) mainContent.classList.remove('expanded');
        localStorage.setItem('sidebarExpanded', 'false');
      }
    });
  }
});
// Make sidebar items accessible via keyboard
document.addEventListener('DOMContentLoaded', function() {
  const sidebarItems = document.querySelectorAll('.sidebar-item');
  sidebarItems.forEach(item => {
    item.setAttribute('tabindex', '0');
    item.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.click();
      }
    });
  });
});
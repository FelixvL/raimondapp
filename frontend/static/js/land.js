$(document).ready(function() {
    $('#searchBar').on('keypress', function(e) {
        if (e.which === 13) { // Check if Enter key is pressed
            var searchTerm = $(this).val();
            if (searchTerm.length > 0) {
                window.location.href = '/search?name=' + encodeURIComponent(searchTerm); // Redirect to search page
            }
        }
    });

    $('#classesModal').on('show.bs.modal', function (e) {
        loadClasses();
    });
});

function registerIemand() {
    window.location.href = '/form';
}

function viewDBList() {
    window.location.href = '/view';
}

function viewPerson() {
    window.location.href = '/personview';
}

function loadClasses() {
    $.ajax({
        url: '/api/classes',
        method: 'GET',
        success: function(response) {
            var classesList = $('#classesList');
            classesList.empty();
            response.forEach(function(classItem) {
                classesList.append(
                    '<li class="list-group-item">' +
                    '<a href="#" onclick="loadStudents(' + classItem.id + ')">' + classItem.name + '</a>' +
                    '</li>'
                );
            });
        },
        error: function(error) {
            console.error('Error fetching classes:', error);
        }
    });
}

function loadStudents(classId) {
    $.ajax({
        url: '/api/class/' + classId + '/students',
        method: 'GET',
        success: function(response) {
            var classesList = $('#classesList');
            classesList.empty();
            classesList.append('<li class="list-group-item"><a href="#" onclick="loadClasses()">Terug naar klassen</a></li>');
            response.students.forEach(function(student) {
                classesList.append(
                    '<li class="list-group-item">' +
                    '<a href="/personview/' + student.id + '">' + student.name + '</a>' +
                    '</li>'
                );
            });
        },
        error: function(error) {
            console.error('Error fetching students:', error);
        }
    });
}

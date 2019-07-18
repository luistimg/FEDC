$(document).ready(function() {
   $('#datatable').dataTable({
        "processing": true,
        "serverSide": true,
        "destroy": true,
        "ajax": URL,
        language: {
            url: JSON_DATA
        }
        });
    $('#datatable')
        .removeClass('display')
        .addClass('table table-striped table-bordered');
});
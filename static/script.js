function faceRegisSubmit() {
    if (!$('#whoru').val()) {
        $('.alert-danger').css('display', 'block');

    } else {
        $('.alert-danger').css('display', 'none');
        $('form').submit();
        $('button').attr("disabled", true)
    }
}
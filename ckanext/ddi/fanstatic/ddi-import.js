$(document).ready(function(){
    $('import-btn').attr('disabled',true);
    $('#field-image-url').change(function(){
        if($(this).val.length != 0){
            $('#import-btn').attr('disabled', false);
        }
    })
    $('#field-image-upload').change(function(){
        if($(this).val.length != 0){
            $('#import-btn').attr('disabled', false);
        }
    })
});

/* Javascript for MasteryCycleXBlock. */
function MasteryCycleXBlock(runtime, element) {
    let $buttonCheckProblems = $('.js-check-problems', element);
    let $body = $('body');
    let loadingClass = 'answer-loading';
    let modalOpenClass = 'dialog-modal-open';
    let handlerCheckProblemsUrl = runtime.handlerUrl(element, 'check_problems');
    $('.problems-wrapper').on('progressChanged', function () {
        let attempts = true;
        $('.problems-wrapper').each(function () {
            if (!$(this).data('attempts-used')) {
                attempts = false;
            }
        })

        if (attempts) {
            $buttonCheckProblems.trigger('click');
        }
    })

    $buttonCheckProblems.click(function() {
        $body.addClass(loadingClass);
        $buttonCheckProblems.prop( "disabled", true );

        $.ajax({
            type: "POST",
            url: handlerCheckProblemsUrl,
            data: JSON.stringify({}),
            success: function (data) {
                $buttonCheckProblems.prop( "disabled", false );
                $body.removeClass(loadingClass).addClass(modalOpenClass);

                $('#next-dialog #msg').html(data.msg);
                $('#next-dialog').dialog({
                    width: 400,
                    resizable: false,
                    draggable: false,
                    buttons: [{
                        text: data.button_text,
                        click: function() {
                            $(this).dialog("close");
                            $body.removeClass(modalOpenClass);

                            if (data.status === 'done') {
                                $buttonCheckProblems.removeClass('js-mastery-cycle-not-done')
                                $('.sequence-nav .button-next').trigger('click');
                            } else if (data.status === 'not_done') {
                                $body.addClass(loadingClass);
                                if (data.url) {
                                    window.location.href = data.url;
                                } else {
                                    window.location.reload();
                                }
                            }
                        }
                    }],
                });
            }
        });
    });
}

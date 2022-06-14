/* Javascript for MasteryCycleXBlock. */
function MasteryCycleXBlock(runtime, element) {
    let $buttonCheckProblems = $('.js-check-problems', element);
    let $buttonNext = $('.js-next-problem', element);
    let $body = $('body');
    let loadingClass = 'answer-loading';
    let modalOpenClass = 'dialog-modal-open';
    let handlerCheckProblemsUrl = runtime.handlerUrl(element, 'check_problems');
    let problemIndex = 0;

    const nextProblem = function() {
        $(`.vert-${problemIndex}`, element).addClass('is-hidden');
        problemIndex += 1;
        $(`.vert-${problemIndex}`, element).removeClass('is-hidden');
        $buttonNext.addClass('disabled');
        $('.current-problem', element).text(problemIndex + 1);
    }

    $('.vert', element).each(function () {
        if ($('.problems-wrapper', $(this)).data('attempts-used') ||
          $('.problems-wrapper', $(this)).data('time-is-over') === 'True') {
            nextProblem();
        }

        if (!$(this).hasClass(`vert-${problemIndex}`)) {
            $(this).addClass('is-hidden');
        }
    });

    $('.problems-wrapper').on('progressChanged timeIsOver', function () {
        let attempts = true;
        $('.problems-wrapper').each(function () {
            if (!$(this).data('attempts-used') && $(this).data('time-is-over') === 'False') {
                attempts = false;
            }
        });

        if (attempts) {
            $buttonCheckProblems.trigger('click');
        } else {
            $buttonNext.removeClass('disabled');
        }
    });

    $buttonCheckProblems.click(function() {
        $body.addClass(loadingClass);
        $buttonCheckProblems.prop("disabled", true);

        $.ajax({
            type: "POST",
            url: handlerCheckProblemsUrl,
            data: JSON.stringify({}),
            success: function (data) {
                $buttonCheckProblems.prop("disabled", false);
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
                                $buttonCheckProblems.removeClass('js-mastery-cycle-not-done');
                                $('.sequence-nav .button-next').trigger('click');
                            } else if (data.status === 'not_done' || data.status === 'error') {
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

    $buttonNext.on('click', nextProblem);
}

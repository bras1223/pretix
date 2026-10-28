/*global $ */

$(function () {
    var $event = $("#id_checkin_event");
    var $list = $("#id_checkin_list");
    if (!$event.length || !$list.length) {
        return;
    }

    var fetchUrl = $event.attr("data-checkinlists-url");
    if (!fetchUrl) {
        return;
    }

    var emptyLabel = "---------";
    var request = null;

    function setOptions(results, selectedId) {
        var html = '<option value="">' + emptyLabel + "</option>";
        (results || []).forEach(function (item) {
            var selected = String(item.id) === String(selectedId) ? " selected" : "";
            html +=
                '<option value="' +
                item.id +
                '"' +
                selected +
                ">" +
                $("<div>").text(item.text).html() +
                "</option>";
        });
        $list.html(html).prop("disabled", false);
    }

    function refetchLists(preserveSelection) {
        var eventId = $event.val();
        var selectedId = preserveSelection ? $list.val() : "";

        if (request && request.abort) {
            request.abort();
        }

        if (!eventId) {
            setOptions([], "");
            $list.prop("disabled", true);
            return;
        }

        $list.prop("disabled", true);
        request = $.getJSON(fetchUrl, {event: eventId})
            .done(function (data) {
                setOptions(data.results || [], selectedId);
            })
            .fail(function (xhr, status) {
                if (status !== "abort") {
                    setOptions([], "");
                }
            });
    }

    $event.on("change", function () {
        refetchLists(false);
    });

    if (!$event.val()) {
        setOptions([], "");
        $list.prop("disabled", true);
    } else if ($list.find('option[value!=""]').length === 0) {
        refetchLists(true);
    }
});

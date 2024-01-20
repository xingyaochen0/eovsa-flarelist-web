document.addEventListener('DOMContentLoaded', function() {
    flatpickr(document.querySelectorAll('.datetime-picker'), {
        enableTime: true,
        dateFormat: "Y-m-d\\TH:i:S",
        defaultHour: 0,
        altFormat: "Y-m-d\\TH:i:S",
        allowInput: true,
        time_24hr: true,
    });

    function renderTable(data) {
        let tableBody = '';
        let keys = ['_id', 'flare_id', 'start', 'end', 'GOES_class', 'link_dspec_data', 'link_movie', 'link_fits'];
        data.forEach((item) => {
            tableBody += '<tr>';
            keys.forEach((key) => { 
                tableBody += '<td>' + (item[key] || '') + '</td>'; // Handle null values
            });
            tableBody += '</tr>';
        });
        $('#flare-list').show();
        $('#flare-list > tbody').html(tableBody);
    }

    function showError(message) {
        // Function to display error messages to the user
        // You can modify this to display the message in a specific div or as a modal
        alert(message);
    }

    $('#query-btn').on('click', function(e) {
        e.preventDefault();
        let start = $('#start').val();
        let end = $('#end').val();

        // Optional: Show loading message or spinner here

        $.ajax({
            url: '/api/flare/query',
            type: "POST",
            data: { 'start': start, 'end': end },
            dataType: "json",
            success: function(response) {
                if (response.error) {
                    showError(response.error);
                } else {
                    // Update the table with the result
                    renderTable(response.result);

                    // Update plot container with Plotly plot
                    $('#plot-container').html(response.plot_html);
                }
            },
            error: function(xhr, status, error) {
                console.error("Error occurred: " + error);
                showError("An error occurred while processing your request.");
            }
        });
    });
});

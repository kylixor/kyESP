var chartT = new Highcharts.Chart({
    chart: {
        renderTo: 'chart-light',
        animation: false,
    },
    series: [
        {
            name: 'Light',
            type: 'line',
            color: '#101D42',
            crisp: false,
            markers: {
                enabled: false,
            },
        },
    ],
    title: {
        text: 'ESP Light Sensor',
    },
    xAxis: {
        type: 'datetime',
        dateTimeLabelFormats: { second: '%H:%M:%S' },
    },
    yAxis: {
        min: 0,
        max: 100,
        title: {
            text: undefined,
        },
    },
    credits: {
        enabled: false,
    },
    time: {
        timezone: 'America/New_York'
    },
});


function plotValue(jsonValue) {

    var keys = Object.keys(jsonValue);

    // for (var i = 0; i < keys.length; i++) {
    for (var i = 0; i < 1; i++) {
        var x = (new Date()).getTime();
        const key = keys[i];
        var y = Number(jsonValue[key]);

        if (chartT.series[i].data.length > 4 * 30) {
            chartT.series[i].addPoint([x, y], true, true, true);
        } else {
            chartT.series[i].addPoint([x, y], true, false, true);
        }
    }
}

if (!!window.EventSource) {
    var source = new EventSource('/events/ldr');

    source.addEventListener('open', function (e) {
        console.log("Events Connected");
    }, false);

    source.addEventListener('error', function (e) {
        if (e.target.readyState != EventSource.OPEN) {
            console.error('Events Disconnected', e)
        } else {
            console.error('Error', e)
        }
    }, false);

    source.addEventListener('ldrData', function (e) {
        var myObj = JSON.parse(e.data);
        plotValue(myObj);
    }, false);
}
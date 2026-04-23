import React from 'react';
import gradient from 'chartjs-plugin-gradient';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { dataLabelColor } from '../../../scoring/dashboard/js/includes/ColorData';

import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, gradient, Tooltip, Legend, Filler, ChartDataLabels);

export function LineChart(props) {
	const options = {
		responsive: true,
		maintainAspectRatio: true,
		interaction: {
			mode: 'index',
			intersect: false,
		},
		plugins: {
			gradient,
			legend: {
				position: 'bottom',
				display: false,
				labels: {
					usePointStyle: true,
					pointStyle: 'rounded',
				},
			},
			title: {
				display: false,
			},
			datalabels: {
				backgroundColor: function (context) {
					return context.dataset.borderColor;
				},
				color: function (context) {
					//We make the condition: if a value of the label is a certain color
					var index = context.dataIndex;
					return dataLabelColor(context.dataset.borderColor);
				},
				font: {
					weight: 'bold',
				},
				formatter: function (value) {
					return Math.round(value) + '%';
				},
				offset: 8,
				borderRadius: 100,
				padding: {
					top: 10,
					right: 5,
					bottom: 10,
					left: 5,
				},
				textAlign: 'center',
			},
			deferred: {
				xOffset: 150, // defer until 150px of the canvas width are inside the viewport
				yOffset: '50%', // defer until 50% of the canvas height are inside the viewport
				delay: 500, // delay of 500 ms after the canvas is considered inside the viewport
			},
		},
		indexAxis: 'x',
		scales: {
			y: {
				suggestedMin: -100,
				suggestedMax: 100,
				grid: {
					display: false,
				},
				borderColor: '#E6E8EC',
				ticks: {
					font: {
						size: 12,
					},
				},
			},
			x: {
				suggestedMin: 0,
				suggestedMax: 100,
				borderColor: '#E6E8EC',
				grid: {
					display: false,
				},
				ticks: {
					font: {
						size: 12,
					},
				},
			},
		},
	};

	const labels = props.labels;

	const data = {
		labels,
		datasets: props.data,
	};
	return <Line options={options} data={data} />;
}

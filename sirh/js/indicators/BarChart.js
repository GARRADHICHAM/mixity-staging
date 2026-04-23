import React from 'react';
import ChartDataLabels from 'chartjs-plugin-datalabels';

import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { dataLabelColor } from '../../../scoring/dashboard/js/includes/ColorData';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ChartDataLabels);

export function BarChart(props) {
	const options = {
		scales: {
			x: {
				display: true,
				suggestedMin: 0,
				suggestedMax: 50,
				border: {
					display: false,
				},
				grid: {
					display: false,
				},
				stacked: true,
			},
			y: {
				display: true,
				suggestedMin: 0,
				suggestedMax: 100,
				stacked: true,
				border: {
					display: false,
				},
				grid: {
					display: false,
				},
				ticks: {
					display: true,
				},
			},
		},
		indexAxis: props.axis,
		elements: {
			bar: {
				borderWidth: 2,
			},
		},
		responsive: true,
		plugins: {
			legend: {
				position: 'bottom',
				display: false,
				labels: {
					/*filter: !this.state.activeBenchmark ? function(item, chart) {
                        // Logic to remove a particular legend item goes here
                        return item.text.includes(this.props.data.data[0][0].label);
                    } : null,*/
					usePointStyle: true,
					pointStyle: 'rounded',
				},
				title: {
					padding: 16,
				},
				borderWidth: 1,
			},
			tooltip: {
				padding: 16,
				backgroundColor: 'rgba(255, 255, 255, 1)',
				borderColor: 'rgba(222, 223, 234, 1)',
				borderWidth: 1,
				titleColor: '#181B3D',
				titleFont: {
					weight: 'bold',
					family: 'DM Sans',
				},
				bodyColor: '#181B3D',
				bodyFont: {
					weight: 'normal',
					family: 'DM Sans',
				},
			},
			callbacks: {
				label: function (data) {
					return `${data.dataset.label[0]} : ${parseFloat(data.formattedValue.replace(',', '.')).toFixed(2)} %`;
				},
			},
		},
	};

	const labels = props.labels;
	const data = {
		labels,
		datasets: props.data,
	};

	return (
		<div className="w-100">
			<h3 className="fw-medium text-center mt-4">{props.title}</h3>
			<Bar options={options} data={data} />
		</div>
	);
}

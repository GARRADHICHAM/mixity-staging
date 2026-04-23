import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { dataLabelColor } from '../../../scoring/dashboard/js/includes/ColorData';

ChartJS.register(ArcElement, Tooltip, Legend);

export function PieChart(props) {
	const data = {
		labels: props.labels,
		datasets: props.data,
	};
	const options = {
		responsive: true,
		plugins: {
			legend: {
				position: 'bottom',
				display: false,
				labels: {
					usePointStyle: true,
					pointStyle: 'rounded',
				},
			},
			title: {
				display: props.title !== undefined,
				text: props.data.title,
				position: 'bottom',
				color: '#181B3D',
				weight: 'bold',
				family: 'DM Sans',
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
				callbacks: {
					label: ({ label, formattedValue }) => `${label} : ${parseFloat(formattedValue.replace(',', '.')).toFixed(2)} %`,
				},
			},
			datalabels: {
				display: true,
				borderWidth: 0,
				color: function (context) {
					//We make the condition: if a value of the label is a certain color
					var index = context.dataIndex;
					return dataLabelColor(context.dataset.backgroundColor[index]);
				},
				font: {
					size: 16,
				},
				formatter: function (value) {
					if (Math.round(value) === 0) return '';
					else return Math.round(value) + '%';
				},
			},
			deferred: {
				xOffset: 150, // defer until 150px of the canvas width are inside the viewport
				yOffset: '50%', // defer until 50% of the canvas height are inside the viewport
				delay: 500, // delay of 500 ms after the canvas is considered inside the viewport
			},
		},
		elements: {
			arc: {
				borderWidth: 0,
			},
		},
	};
	return (
		<div className="w-100">
			<h3 className="fw-medium text-center mt-4">{props.title}</h3>
			<Pie data={data} options={options} />
		</div>
	);
}

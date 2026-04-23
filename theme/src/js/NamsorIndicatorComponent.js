import React, { useState, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { HierarchicalScale } from 'chartjs-plugin-hierarchical';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import * as XLSX from 'xlsx';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, HierarchicalScale, ChartDataLabels);

const slugify = (str) =>
	str
		.toLowerCase()
		.trim()
		.replace(/[^\w\s-]/g, '')
		.replace(/[\s_-]+/g, '-')
		.replace(/^-+|-+$/g, '');

/** Download contents as a file
 * Source: https://stackoverflow.com/questions/14964035/how-to-export-javascript-array-info-to-csv-on-client-side
 */
function downloadBlob(content, filename, contentType) {
	// Create a blob
	//var blob = new Blob([content], { type: contentType });
	const blob = b64toBlob(content, contentType);
	const url = URL.createObjectURL(blob);

	// Create a link to download it
	const pom = document.createElement('a');
	pom.href = url;
	pom.setAttribute('download', filename);
	pom.click();
}

/*
    Convert a list of rows (like CSV) to a XLSX file (Base64)
 */
export const convertArrayToExcelBuffer = (array) => {
	const wb = XLSX.utils.book_new();
	const newWs = XLSX.utils.aoa_to_sheet(array);
	XLSX.utils.book_append_sheet(wb, newWs);
	const rawExcel = XLSX.write(wb, { type: 'base64' });
	return rawExcel;
};

/*
    Convert a base64 string to a Blob file in order to download it
 */
export const b64toBlob = (b64Data, contentType = '', sliceSize = 512) => {
	const byteCharacters = atob(b64Data);
	const byteArrays = [];

	for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
		const slice = byteCharacters.slice(offset, offset + sliceSize);

		const byteNumbers = new Array(slice.length);
		for (let i = 0; i < slice.length; i++) {
			byteNumbers[i] = slice.charCodeAt(i);
		}

		const byteArray = new Uint8Array(byteNumbers);
		byteArrays.push(byteArray);
	}

	const blob = new Blob(byteArrays, { type: contentType });
	return blob;
};

export default function NamsorIndicatorComponent(props) {
	let delayed;
	let chart = useRef(null);

	const options = {
		responsive: true,
		maintainAspectRatio: false,
		layout: {
			padding: {
				// add more space at the bottom for the hierarchy
				bottom: 65,
			},
		},
		animation: {
			onComplete: () => {
				delayed = true;
			},
			delay: (context) => {
				let delay = 0;
				if (context.type === 'data' && context.mode === 'default' && !delayed) {
					delay = context.dataIndex * 300 + context.datasetIndex * 100;
				}
				return delay;
			},
		},
		plugins: {
			title: {
				display: false,
				//text: 'Je veux mon titre ici stp :)',
			},
			legend: {
				display: false,
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
				color: '#181B3D',
				font: function (context) {
					var w = context.chart.width;
					return {
						size: 16,
						weight: 'bold',
					};
				},
				display: function (context) {
					return context.dataset.data[context.dataIndex];
				},
				formatter: function (value) {
					return Math.round(value) + '%';
				},
			},
			deferred: {
				xOffset: 150, // defer until 150px of the canvas width are inside the viewport
				yOffset: '50%', // defer until 50% of the canvas height are inside the viewport
				delay: 500, // delay of 500 ms after the canvas is considered inside the viewport
			},
		},
		// Core options
		scales: {
			x: {
				type: 'hierarchical',
				hierarchyLabelPosition: 'below',
				hierarchyGroupLabelPosition: 'center',
				hierarchySpanWidth: 1,
				hierarchySpanColor: '#E6E8EC',
				hierarchyBoxColor: '#E6E8EC',
				title: {
					color: '#181B3D',
					font: {
						family: 'DM Sans',
						size: 16,
					},
				},
				border: {
					display: true,
				},
				grid: {
					display: false,
				},
				ticks: {
					color: '#181B3D',
					font: {
						family: 'DM Sans',
						size: 16,
					},
				},
			},
			y: {
				min: 0,
				max: 100,
				ticks: {
					beginAtZero: true,
					color: '#181B3D',
					font: {
						family: 'DM Sans',
						size: 16,
					},
				},
				border: {
					display: true,
				},
				grid: {
					display: false,
				},
			},
		},
		// End Core options
	};

	var selectedResults = props.result;
	var data = {
		// define label tree
		labels: selectedResults.labels,
		datasets: [
			{
				label: 'Ethnie',
				backgroundColor: ['#00694D', '#00F5B4', '#00A87B', '#00B585', '#008F69'],
				borderRadius: Number.MAX_VALUE,
				borderSkipped: 'bottom',
				tree: selectedResults.data,
				data: {
					data_count: selectedResults.labels,
					min: 0,
					max: 100,
				},
				datalabels: {
					align: 'end',
					anchor: 'end',
				},
			},
		],
	};

	function collapseLabels(labels, update = true) {
		labels.forEach((label) => {
			label.expand = false;
			label.hidden = false;
			if (label.children.length > 0) {
				collapseLabels(label.children, false);
			}
		});
		if (update) {
			chart.current.update();
			chart.current.render();
		}
    }

	function exportToCsv(labels, data, level = 0, finalExport = true) {
		let results = [];
		labels.forEach((label, i) => {
			if (typeof label === 'string') {
				if (finalExport)
					results.push([...Array(level * 2).fill(''), label, data[i].toFixed(2) + ' %']);
			} else {
				results = [
					...results,
					[...Array(level * 2).fill(''), label.label, data[i].value.toFixed(2) + ' %'],
					...exportToCsv(label.children, data[i].children, level + 1, false),
				];
			}
		});
		if (finalExport) {
			results = [[selectedResults.label], [], ...results];
			downloadBlob(convertArrayToExcelBuffer(results), slugify(selectedResults.label) + '.xlsx', 'text/csv;charset=utf-8;');
		}
		return results;
	}

	return (
		<React.Fragment>
			<h2 className="w-100 text-center title--h2 mt-4 mb-5">{selectedResults.label}</h2>
			<div className="w-100 d-flex justify-content-between mb-5 mx-5">
				<div className="fw-medium-2">
					{gettext('Indice de confiance : ')}
					{Math.round(selectedResults.confidence)}%
					<span className="tooltip mx-3">
						<div className="tooltip__icon">?</div>
						<span className="tooltip__text">{gettext("Probablité de l'exactitude des donnée")}</span>
					</span>
				</div>
				<div className="processed_collaborators">
					{gettext('Collaborateurs (f/h/nb) traités : ')}
					<span className="fw-bold">{selectedResults.processed_collaborators}</span>
					<span className="fw-bold"> / {selectedResults.processed_collaborators + selectedResults.unprocessed_collaborators}</span>
					{gettext('')}
				</div>
			</div>
			<div className="w-100 d-flex justify-content-center">
				<div className="m-auto mx-5 w-100" style={{ height: '60vh' }}>
					<Bar options={options} data={props.data ? props.data : data} key={JSON.stringify(data)} ref={chart} />
				</div>
			</div>
			<div className="w-100 d-flex justify-content-around align-items-center">
                <a
					className="button button_dashboard border p-2"
					role="button"
					onClick={() => {
						exportToCsv(selectedResults.labels, selectedResults.data);
					}}
					>
					<i className="bi bi-cloud-download"></i>
					{gettext('Excel')}
				</a>
				<a
					className="button button_dashboard border p-2"
					role="button"
					onClick={() => {
						chart.current.data.labels = [...chart.current.data.rootNodes];
						collapseLabels(chart.current.data.rootNodes);
					}}
					>
					{gettext('Tout réduire')}
				</a>
			</div>
		</React.Fragment>
	);
}

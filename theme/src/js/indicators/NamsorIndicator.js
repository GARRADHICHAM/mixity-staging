import React, { useState, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import NamsorIndicatorComponent from '../NamsorIndicatorComponent';


export default function NamsorIndicator(props) {
	const [selectedResults, setSelectedResults] = useState(props.results[0]);
	const [data, setData] = useState({
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
	});

	function changeSource(selected) {
		setSelectedResults(selected);
		setData({
			labels: selected.labels,
			datasets: [
				{
					...data.datasets[0],
					tree: selected.data,
					data: {
						data_count: selectedResults.labels,
						min: 0,
						max: 100,
					},
				},
			],
		});
	}

	return (
		<React.Fragment>
			{props.results.length > 1 && (
				<div className="w-100 d-flex justify-content-center align-items-center mb-4">
					<select
						className="select_indicator"
						onChange={(el) => {
							changeSource(props.results[parseInt(el.currentTarget.value)]);
						}}
						style={{ width: "30%", minWidth: "fit-content" }}
					>
						{props.results.map((element, i) => {
							return (
								<option key={i} value={i}>
									{element.name}
								</option>
							);
						})}
					</select>
				</div>
			)}
			<NamsorIndicatorComponent result={selectedResults} data={data} />
		</React.Fragment>
	);
}

export function renderNamsorIndicator(id, results) {
	const rootElement = document.getElementById('namsor_indicator_' + id);
	createRoot(rootElement).render(<NamsorIndicator results={results} />);
}

import React, { Component } from 'react';
import gradient from 'chartjs-plugin-gradient';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { getColors, dataLabelColor } from './ColorData';

import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, gradient, Tooltip, Legend, Filler, ChartDataLabels);

export default class LineChart extends Component {
	constructor(props) {
		super(props);
		this.state = {
			activeBenchmark: false,
			options: {},
			data: {},
			dataIsSet: false,
			activeIndex: 0,
		};
	}

	legendDescItem(color, value, isEntity = false) {
		return (
			<div className="d-inline-flex align-items-center py-2">
				<div>
					<div className="indic-score" style={{ backgroundColor: `${color}` }}></div>
				</div>
				{isEntity ? <span className="legend_value fw-bold">{value}</span> : <span className="legend_value">{value}</span>}
			</div>
		);
	}

	componentDidMount() {
		//Defining Bar options
		let delayed = false;
		const options = {
			responsive: true,
			maintainAspectRatio: false,
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
					suggestedMin: function (question) {
						return question === '' ? -100 : 0;
					},
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
		if (!this.props.data.selector && this.props.data.values[0] && this.props.data.values[0][0]) {
			var data = {
				labels: this.props.data.labels,
				datasets: [
					{
						label: 'Femmes',
						data: this.props.data.values[0],
						gradient: {
							backgroundColor: {
								axis: 'y',
								colors: {
									0: 'transparent',
									10: getColors(this.props.category + '_list', this.props.data.colors, 0.1)[0],
									50: getColors(this.props.category + '_list', this.props.data.colors, 0.5)[0],
									100: getColors(this.props.category + '_list', this.props.data.colors)[0],
								},
							},
						},
						borderColor: getColors(this.props.category + '_list', this.props.data.colors)[0],
						fill: {
							target: 'origin',
						},
						tension: 0.4,
					},
					{
						label: 'Hommes',
						data: this.props.data.values[1],
						gradient: {
							backgroundColor: {
								axis: 'y',
								colors: {
									0: 'transparent',
									10: getColors(this.props.category + '_list', this.props.data.colors, 0.1)[1],
									50: getColors(this.props.category + '_list', this.props.data.colors, 0.5)[1],
									100: getColors(this.props.category + '_list', this.props.data.colors)[1],
								},
							},
						},
						borderColor: getColors(this.props.category + '_list', this.props.data.colors)[1],
						fill: {
							target: 'origin',
						},
						tension: 0.4,
					},
					{
						label: 'Moyenne dans mon secteur',
						data: this.props.data.selector ? this.props.data.meanscore_sector_values[0] : this.props.data.meanscore_sector_values,
						borderColor: getColors('meanscore_sector', [1]),
						backgroundColor: getColors('meanscore_sector', [1]),
						datalabels: {
							color: (chart) => {
								//We make the condition: if a value of the label is a certain color
								return dataLabelColor(chart.dataset.backgroundColor[chart.dataIndex]);
							},
							font: {
								weight: 'bold',
							},
						},
						tension: 0.4,
						hidden: !this.state.activeBenchmark,
						fill: false,
					},
					{
						label: 'Moyenne Globale',
						data: this.props.data.selector ? this.props.data.meanscore_global_values[0] : this.props.data.meanscore_global_values,
						borderColor: getColors('meanscore_global', [1]),
						backgroundColor: getColors('meanscore_global', [1]),
						tension: 0.4,
						hidden: !this.state.activeBenchmark,
						fill: false,
					},
				],
			};
		} else {
			var data = {
				labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
				datasets: [
					{
						label: 'Entreprise',
						data: this.props.data.selector ? this.props.data.values[0] : this.props.data.values,
						gradient: {
							backgroundColor: {
								axis: 'y',
								colors: {
									0: 'transparent',
									10: getColors(this.props.category, [1], 0.1),
									50: getColors(this.props.category, [1], 0.5),
									100: getColors(this.props.category, [1]),
								},
							},
						},
						borderColor: getColors(this.props.category, [1]),
						fill: {
							target: 'origin',
						},
						tension: 0.4,
					},
					{
						label: 'Moyenne dans mon secteur',
						data: this.props.data.selector ? this.props.data.meanscore_sector_values[0] : this.props.data.meanscore_sector_values,
						borderColor: getColors('meanscore_sector', [1]),
						backgroundColor: getColors('meanscore_sector', [1]),
						tension: 0.4,
						hidden: !this.state.activeBenchmark,
						fill: false,
					},
					{
						label: 'Moyenne Globale',
						data: this.props.data.selector ? this.props.data.meanscore_global_values[0] : this.props.data.meanscore_global_values,
						borderColor: getColors('meanscore_global', [1]),
						backgroundColor: getColors('meanscore_global', [1]),
						tension: 0.4,
						hidden: !this.state.activeBenchmark,
						fill: false,
					},
				],
			};
		}

		this.setState({
			options: options,
			data: data,
			dataIsSet: true,
		});
	}

	changeBenchmark() {
		if (this.props.data.selector) {
			var data = {
				labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
				datasets: [
					{
						label: 'Entreprise',
						data: this.props.data.values[this.state.activeIndex],
						gradient: {
							backgroundColor: {
								axis: 'y',
								colors: {
									0: 'transparent',
									10: getColors(this.props.category, [1], 0.1),
									50: getColors(this.props.category, [1], 0.5),
									100: getColors(this.props.category, [1]),
								},
							},
						},
						fill: {
							target: 'origin',
						},
					},
					{
						label: 'Moyenne dans mon secteur',
						data: this.props.data.meanscore_sector_values[this.state.activeIndex],
						type: 'line',
						borderColor: getColors('meanscore_sector', [1]),
						backgroundColor: getColors('meanscore_sector', [1]),
						hidden: this.state.activeBenchmark,
					},
					{
						label: 'Moyenne globale',
						data: this.props.data.meanscore_global_values[this.state.activeIndex],
						borderColor: getColors('meanscore_global', [1]),
						backgroundColor: getColors('meanscore_global', [1]),
						type: 'line',
						hidden: this.state.activeBenchmark,
					},
				],
			};
		} else {
			var data = {
				labels: this.props.data.labels,
				datasets: [
					{
						label: 'Entreprise',
						data: this.props.data.values,
						gradient: {
							backgroundColor: {
								axis: 'y',
								colors: {
									0: 'transparent',
									10: getColors(this.props.category, [1], 0.1),
									50: getColors(this.props.category, [1], 0.5),
									100: getColors(this.props.category, [1]),
								},
							},
						},
						fill: {
							target: 'origin',
						},
					},
					{
						label: 'Moyenne dans mon secteur',
						data: this.props.data.meanscore_sector_values,
						type: 'line',
						borderColor: getColors('meanscore_sector', [1]),
						backgroundColor: getColors('meanscore_sector', [1]),
						hidden: this.state.activeBenchmark,
					},
					{
						label: 'Moyenne globale',
						data: this.props.data.meanscore_global_values,
						borderColor: getColors('meanscore_global', [1]),
						backgroundColor: getColors('meanscore_global', [1]),
						type: 'line',
						hidden: this.state.activeBenchmark,
					},
				],
			};
		}

		this.setState({
			activeBenchmark: !this.state.activeBenchmark,
			data: data,
		});
	}

	changeDatas(e) {
		var data = {
			labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
			datasets: [
				{
					label: 'Entreprise',
					data: this.props.data.values[e.target.value],
					gradient: {
						backgroundColor: {
							axis: 'y',
							colors: {
								0: 'transparent',
								10: getColors(this.props.category, [1], 0.1),
								50: getColors(this.props.category, [1], 0.5),
								100: getColors(this.props.category, [1]),
							},
						},
					},
					fill: {
						target: 'origin',
					},
				},
				{
					label: 'Moyenne dans mon secteur',
					data: this.props.data.meanscore_sector_values[e.target.value],
					type: 'line',
					borderColor: getColors('meanscore_sector', [1]),
					backgroundColor: getColors('meanscore_sector', [1]),
					hidden: !this.state.activeBenchmark,
				},
				{
					label: 'Moyenne globale',
					data: this.props.data.meanscore_global_values[e.target.value],
					borderColor: getColors('meanscore_global', [1]),
					backgroundColor: getColors('meanscore_global', [1]),
					type: 'line',
					hidden: !this.state.activeBenchmark,
				},
			],
		};

		this.setState({
			activeIndex: e.target.value,
			data: data,
		});
	}

	render() {
		return (
			<React.Fragment>
				{this.props.data.selector && (
					<select className="select_indicator mb-5" name="selectedSubquestion" defaultValue="0" onChange={(e) => this.changeDatas(e)}>
						{this.props.data.selector_labels.map((label, index) => {
							return (
								<option key={index} value={`${index}`}>
									{label}
								</option>
							);
						})}
					</select>
				)}
				{this.props.data.perimeter && (
					<h4 className="w-100 fw-medium text-center mb-4" style={{ fontWeight: '400', fontSize: '12px' }}>
						{this.props.data.perimeter}
					</h4>
				)}
				<div className="line_container w-100" style={{ position: 'relative', height: '40vh' }}>
					{this.state.dataIsSet && (
						<React.Fragment>
							<Line options={this.state.options} data={this.state.data} />
						</React.Fragment>
					)}
				</div>
				<div className="w-100 d-flex flex-column align-items-center">
					{this.props.data.id === 2021054 || this.props.data.id === 2021018 ? (
						<React.Fragment>
							<div className="d-flex justify-content-between mt-2 w-100" style={{ fontSize: '.8rem' }}>
								<p>{gettext('Risque faible')}</p>
								<p>{gettext('Risque élevé')}</p>
							</div>
						</React.Fragment>
					) : (
						''
					)}
					{this.props.data.id === 20210111 ? (
						<React.Fragment>
							<div className="d-flex justify-content-between mt-2 w-100" style={{ fontSize: '.8rem' }}>
								<p>{gettext('Mal préparé')}</p>
								<p>{gettext('Bien préparé')}</p>
							</div>
						</React.Fragment>
					) : (
						''
					)}
					{this.state.dataIsSet && (
						<div className="w-100 circularChart_legend d-flex justify-content-center align-items-center flex-wrap mt-3">
							{this.state.dataIsSet && !this.props.data.selector && this.props.data.values[0] && this.props.data.values[0][0] ? (
								<div className="w-100 d-flex justify-content-center">
									<div className="legend_item pe-2">
										{this.legendDescItem(getColors(this.props.category + '_list', this.props.data.colors)[0], gettext('Femmes'))}
									</div>
									<div className="legend_item">
										{this.legendDescItem(getColors(this.props.category + '_list', this.props.data.colors)[1], gettext('Hommes'))}
									</div>
								</div>
							) : (
								<div className="legend_item">{this.legendDescItem(getColors(this.props.category, [1]), gettext('Entreprise'), true)}</div>
							)}
							{this.state.activeBenchmark === true ? (
								<div className="legend_item px-2">{this.legendDescItem(getColors('meanscore_sector', [1]), gettext('Moyenne Secteur'))}</div>
							) : (
								''
							)}
							{this.state.activeBenchmark === true ? (
								<div className="legend_item">{this.legendDescItem(getColors('meanscore_global', [1]), gettext('Moyenne Globale'))}</div>
							) : (
								''
							)}
						</div>
					)}
					{this.props.isHuman && (
						<>
							{this.state.dataIsSet && !this.props.data.selector && this.props.data.values[0] && this.props.data.values[0][0] ? (
								''
							) : (
								<React.Fragment>
									<div className="d-flex gap-2 justify-content-center align-items-center my-3">
										<div className="d-flex align-items-center">
											<input
												type="checkbox"
												id={`input-filter-${this.props.data.title}`}
												value={this.state.activeBenchmark}
												onClick={() => this.changeBenchmark()}
											></input>
											<label className="ps-2">{gettext('Afficher le Benchmark')}</label>
										</div>
									</div>
								</React.Fragment>
							)}
						</>
					)}
				</div>
			</React.Fragment>
		);
	}
}

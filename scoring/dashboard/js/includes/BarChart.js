import React, { Component } from 'react';
import ChartDataLabels from 'chartjs-plugin-datalabels';

import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { getColors, dataLabelColor } from './ColorData';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ChartDataLabels);

export default class BarChart extends Component {
	constructor(props) {
		super(props);
		this.state = {
			activeBenchmark: false,
			options: {},
			data: {},
			dataIsSet: false,
			activeIndex: 0,
			specialLabel: false,
		};
	}

	create_stacked_datasets(values, activeIndex, bgColor, index, stack) {
		return {
			label: this.props.data.selector ? [this.props.data.labels[activeIndex][index]] : [this.props.data.labels[index]],
			data: this.props.data.selector ? [values[activeIndex][index]] : [values[index]],
			backgroundColor: this.props.data.labels[index] === '' ? '#E6E8EC' : bgColor,
			borderWidth: 0,
			borderRadius: 8,
			order: index,
			datalabels: {
				display: this.props.data.labels[index] === '' ? false : true,
				align: 'center',
				anchor: 'center',
				color: (chart) => {
					//We make the condition: if a value of the label is a certain color
					return dataLabelColor(chart.dataset.backgroundColor);
				},
				font: {
					weight: 'bold',
				},
				formatter: (value) => {
					if (Math.round(value) === 0) return '';
					else return Math.round(value) + '%';
				},
				offset: 8,
				textAlign: 'center',
			},
			stack: stack,
		};
	}

	create_basic_datasets(label, values, activeIndex, bgColors, order) {
		return {
			label: label,
			data: this.props.data.selector ? values[activeIndex] : values,
			backgroundColor: bgColors,
			borderWidth: 0,
			borderRadius: 100,
			order: order,
			datalabels: {
				align: 'end',
				anchor: 'start',
				color: (chart) => {
					//We make the condition: if a value of the label is a certain color
					return dataLabelColor(chart.dataset.backgroundColor[chart.dataIndex]);
				},
				font: {
					weight: 'bold',
				},
				formatter: (value) => {
					if (Math.round(value) === 0) return '';
					else return Math.round(value) + '%';
				},
				textAlign: 'center',
			},
		};
	}

	create_basic_line_datasets(label, values, activeIndex, bgColors, order, benchmark) {
		return {
			label: label,
			data: this.props.data.selector ? values[activeIndex] : values,
			type: 'line',
			borderColor: bgColors,
			backgroundColor: bgColors,
			hidden: benchmark,
			order: order,
			datalabels: {
				align: 'center',
				anchor: 'center',
				color: (chart) => {
					//We make the condition: if a value of the label is a certain color
					return dataLabelColor(chart.dataset.backgroundColor);
				},
				font: {
					weight: 'bold',
				},
				backgroundColor: (chart) => {
					return chart.dataset.backgroundColor;
				},
				formatter: (value) => {
					if (Math.round(value) === 0) return '';
					else return Math.round(value) + '%';
				},
				textAlign: 'center',
				borderRadius: 100,
				padding: {
					top: 10,
					right: 5,
					bottom: 10,
					left: 5,
				},
			},
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
		var options = {
			scales: {
				y: {
					display: this.props.data.display_params.stacked ? false : true,
					border: {
						display: this.props.data.display_params.stacked ? false : true,
						color: '#E6E8EC',
					},
					grid: {
						display: false,
					},
				},
				x: {
					display: false,
					suggestedMin: 0,
					suggestedMax: 100,
					stacked: this.props.data.display_params.stacked,
					border: {
						display: this.props.data.display_params.stacked ? false : true,
						color: '#E6E8EC',
					},
					grid: {
						display: true,
					},
					ticks: {
						callback: function (value, index, values) {
							return ''; // Retourne un label vide pour masquer les labels de l'axe x
						},
					},
				},
			},
			indexAxis: 'x',
			elements: {
				bar: {
					borderWidth: 2,
				},
			},
			responsive: true,
			maintainAspectRatio: false,
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
					callbacks: {
						label: function (data) {
							return `${data.dataset.label[0]} : ${parseFloat(data.formattedValue.replace(',', '.')).toFixed(2)} %`;
						},
					},
				},
				title: {
					display: false,
				},
			},
		};

		var special_label_case = false;
		//Set datasets differently if it's stacked bars or not
		if (this.props.data.display_params.stacked) {
			var data = {
				labels: [''],
				datasets: [],
			};
			if (this.props.data.selector) {
				if (this.props.data.values[0].reduce((accumulator, currentValue) => accumulator + Math.round(currentValue), 0) < 100) {
					special_label_case = true;
					this.props.data.values.map((values_list, index) => {
						if (this.props.data.labels.length < 6) {
							this.props.data.labels.map((label_list) => {
								label_list.push(gettext('Non'));
							});
						}
						values_list.push(100 - values_list.reduce((accumulator, currentValue) => accumulator + currentValue, 0));
						this.props.data.meanscore_sector_values[index].push(
							100 - this.props.data.meanscore_sector_values[index].reduce((accumulator, currentValue) => accumulator + currentValue, 0),
						);
						this.props.data.meanscore_global_values[index].push(
							100 - this.props.data.meanscore_global_values[index].reduce((accumulator, currentValue) => accumulator + currentValue, 0),
						);
					});
				}
			} else {
				if (this.props.data.values.reduce((accumulator, currentValue) => accumulator + Math.round(currentValue), 0) < 100) {
					special_label_case = true;
					if (this.props.data.labels.length < 6) {
						this.props.data.labels.push(gettext('Non'));
					}
					this.props.data.values.push(100 - this.props.data.values.reduce((accumulator, currentValue) => accumulator + currentValue, 0));
					this.props.data.meanscore_sector_values.push(
						100 - this.props.data.meanscore_sector_values.reduce((accumulator, currentValue) => accumulator + currentValue, 0),
					);
					this.props.data.meanscore_global_values.push(
						100 - this.props.data.meanscore_global_values.reduce((accumulator, currentValue) => accumulator + currentValue, 0),
					);
				}
			}
			var max = this.props.data.selector ? this.props.data.values[0].length : this.props.data.values.length;
			for (let index = 0; index < max; index++) {
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.values,
						0,
						getColors(this.props.category + '_list', this.props.data.colors)[index],
						index,
						'Stack 0',
					),
				);
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.meanscore_sector_values,
						0,
						getColors('meanscore_sector_list', this.props.data.colors)[index],
						index,
						'Stack 1',
					),
				);
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.meanscore_global_values,
						0,
						getColors('meanscore_global_list', this.props.data.colors)[index],
						index,
						'Stack 2',
					),
				);
			}
		} else {
			var data = {
				labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
				datasets: [
					this.create_basic_datasets('Entreprise', this.props.data.values, 0, getColors(this.props.category + '_list', this.props.data.colors), 2),
					this.create_basic_line_datasets('Secteur', this.props.data.meanscore_sector_values, 0, getColors('meanscore_sector', [1]), 1, true),
					this.create_basic_line_datasets('Global', this.props.data.meanscore_global_values, 0, getColors('meanscore_global', [1]), 0, true),
				],
			};
		}

		this.setState({
			options: options,
			data: data,
			dataIsSet: true,
			specialLabel: special_label_case,
		});
	}

	changeBenchmark() {
		//Set datasets differently if it's stacked bars or not
		if (this.props.data.display_params.stacked) {
			var data = {
				labels: [''],
				datasets: [],
			};
			for (let index = 0; index < this.props.data.values[0].length; index++) {
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.values,
						this.state.activeIndex,
						getColors(this.props.category + '_list', this.props.data.colors)[index],
						index,
						'Stack 0',
					),
				);
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.meanscore_sector_values,
						this.state.activeIndex,
						getColors('meanscore_sector_list', this.props.data.colors)[index],
						index,
						'Stack 1',
					),
				);
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.meanscore_global_values,
						this.state.activeIndex,
						getColors('meanscore_global_list', this.props.data.colors)[index],
						index,
						'Stack 2',
					),
				);
			}
		} else {
			var data = {
				labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
				datasets: [
					this.create_basic_datasets(
						'Entreprise',
						this.props.data.values,
						this.state.activeIndex,
						getColors(this.props.category + '_list', this.props.data.colors),
						2,
					),
					this.create_basic_line_datasets(
						'Secteur',
						this.props.data.meanscore_sector_values,
						this.state.activeIndex,
						getColors('meanscore_sector', [1]),
						1,
						this.state.activeBenchmark,
					),
					this.create_basic_line_datasets(
						'Global',
						this.props.data.meanscore_global_values,
						this.state.activeIndex,
						getColors('meanscore_global', [1]),
						0,
						this.state.activeBenchmark,
					),
				],
			};
		}

		this.setState({
			activeBenchmark: !this.state.activeBenchmark,
			data: data,
		});
	}

	changeDatas(e) {
		e.preventDefault();
		if (this.props.data.display_params.stacked) {
			var data = {
				labels: [''],
				datasets: [],
			};
			for (let index = 0; index < this.props.data.values[0].length; index++) {
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.values,
						e.target.value,
						getColors(this.props.category + '_list', this.props.data.colors)[index],
						index,
						'Stack 0',
					),
				);
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.meanscore_sector_values,
						e.target.value,
						getColors('meanscore_sector_list', this.props.data.colors)[index],
						index,
						'Stack 1',
					),
				);
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.meanscore_global_values,
						e.target.value,
						getColors('meanscore_global_list', this.props.data.colors)[index],
						index,
						'Stack 2',
					),
				);
			}
		} else {
			var data = {
				labels: this.props.data.selector ? this.props.data.labels[e.target.value] : this.props.data.labels,
				datasets: [
					this.create_basic_datasets(
						'Entreprise',
						this.props.data.values,
						e.target.value,
						getColors(this.props.category + '_list', this.props.data.colors),
						2,
					),
					this.create_basic_line_datasets(
						'Secteur',
						this.props.data.meanscore_sector_values,
						e.target.value,
						getColors('meanscore_sector', [1]),
						1,
						!this.state.activeBenchmark,
					),
					this.create_basic_line_datasets(
						'Global',
						this.props.data.meanscore_global_values,
						e.target.value,
						getColors('meanscore_global', [1]),
						0,
						!this.state.activeBenchmark,
					),
				],
			};
		}

		this.setState({
			data: data,
			activeIndex: e.target.value,
		});
	}

	render() {
		return (
			<React.Fragment>
				{this.props.data.selector && (
					<select className="select_indicator mb-5" name="selectedSubquestion" defaultValue="0" onChange={(e) => this.changeDatas(e)}>
						{this.props.data.selector_labels.map((label, index) => {
							return (
								<option key={index} value={index}>
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
				<div
					className="bar_container w-100"
					style={{ position: 'relative', height: this.props.data.selector && this.props.data.display_params.stacked ? '40vh' : '48vh' }}
				>
					{this.state.dataIsSet && (
						<React.Fragment>
							{this.state.data.datasets[0].data.length === 0 ? (
								<div className="d-flex justify-content-center align-items-center">
									<b style={{ fontSize: '24px' }}>No data available</b>
								</div>
							) : (
								<Bar options={this.state.options} data={this.state.data} />
							)}
						</React.Fragment>
					)}
				</div>
				<div className="d-flex flex-column align-items-center">
					{this.state.dataIsSet && (
						<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap mt-3">
							{this.props.data.selector
								? this.props.data.labels[this.state.activeIndex].map((label, index) => {
										return (
											<div key={index} className="d-inline-flex align-items-center py-2 me-3">
												<div>
													<div
														className="indic-score pe-2"
														style={{
															backgroundColor: `${(this.state.specialLabel && label === gettext('Non') || index === 5) ? '#E6E8EC' : getColors(this.props.category + '_list', [this.props.data.colors[index]])[0]}`,
														}}
													></div>
												</div>
												<span className="legend_value">{label}</span>
											</div>
										);
									})
								: this.props.data.labels.map((label, index) => {
										return (
											<div key={index} className="d-inline-flex align-items-center py-2 me-3">
												<div>
													<div
														className="indic-score pe-2"
														style={{
															backgroundColor: `${(this.state.specialLabel && label === gettext('Non') || index === 5) ? '#E6E8EC' : getColors(this.props.category + '_list', [this.props.data.colors[index]])[0]}`,
														}}
													></div>
												</div>
												<span className="legend_value">{label}</span>
											</div>
										);
									})}
							<div className="w-100 d-flex justify-content-center">
								{this.state.activeBenchmark === true || this.props.data.display_params.stacked ? (
									<div className="legend_item px-2">
										{this.legendDescItem(getColors('meanscore_sector', [1]), gettext('Moyenne Secteur'))}
									</div>
								) : (
									''
								)}
								{this.state.activeBenchmark === true || this.props.data.display_params.stacked ? (
									<div className="legend_item">{this.legendDescItem(getColors('meanscore_global', [1]), gettext('Moyenne Globale'))}</div>
								) : (
									''
								)}
							</div>
						</div>
					)}
					{this.state.dataIsSet && this.props.data.display_params.stacked === false && (
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
				</div>
			</React.Fragment>
		);
	}
}

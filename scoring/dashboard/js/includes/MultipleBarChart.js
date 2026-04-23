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
			activeValues: 0,
			options: {},
			data: {},
			dataIsSet: false,
		};
	}

	legendDescItem(color, value) {
		return (
			<div className="d-inline-flex align-items-center py-2">
				<div>
					<div className="indic-score" style={{ backgroundColor: `${color}` }}></div>
				</div>
				<span className="legend_value">{value}</span>
			</div>
		);
	}

	create_stacked_datasets(values, activeIndex, bgColor, stack, thickness, benchmark) {
		if (thickness === 25 && benchmark) {
			thickness = 50;
			benchmark = false;
		}
		return {
			label: this.props.data.labels[activeIndex],
			data: values[activeIndex],
			backgroundColor: bgColor,
			borderWidth: 0,
			borderRadius: 8,
			barThickness: thickness,
			hidden: benchmark,
			// order: index,
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

	componentDidMount() {
		//Defining Bar options
		var options = {
			scales: {
				x: {
					display: true,
					border: {
						display: false,
					},
					grid: {
						display: false,
					},
					ticks: {
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
			indexAxis: 'y',
			interaction: {
				intersect: false,
			},
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					position: 'left',
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
						label: ({ label, formattedValue }) => `${label} : ${parseFloat(formattedValue.replace(',', '.')).toFixed(2)} %`,
					},
				},
				title: {
					display: false,
				},
			},
		};

		var data = {
			labels: this.props.data.labels,
			datasets: [],
		};

		if (!this.props.data.selector) {
			this.props.data.values.map((values_list, first_index) => {
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.values,
						first_index,
						getColors(this.props.category + '_list', this.props.data.colors)[first_index],
						'Stack 0',
						50,
						false,
					),
				);
				if (this.props.data.meanscore_sector_values[first_index]) {
					data.datasets.push(
						this.create_stacked_datasets(
							this.props.data.meanscore_sector_values,
							first_index,
							getColors('meanscore_sector_list', this.props.data.colors)[first_index],
							'Stack 1',
							15,
							true,
						),
					);
				}
				if (this.props.data.meanscore_global_values[first_index]) {
					data.datasets.push(
						this.create_stacked_datasets(
							this.props.data.meanscore_global_values,
							first_index,
							getColors('meanscore_global_list', this.props.data.colors)[first_index],
							'Stack 2',
							15,
							true,
						),
					);
				}
			});
		} else {
			this.props.data.values[0].map((values_list, first_index) => {
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.values[0],
						first_index,
						getColors(this.props.category + '_list', this.props.data.colors)[first_index],
						'Stack 0',
						50,
						false,
					),
				);
				if (this.props.data.meanscore_sector_values[0]) {
					data.datasets.push(
						this.create_stacked_datasets(
							this.props.data.meanscore_sector_values[0],
							first_index,
							getColors('meanscore_sector_list', this.props.data.colors)[first_index],
							'Stack 1',
							15,
							true,
						),
					);
				}
				if (this.props.data.meanscore_global_values[0]) {
					data.datasets.push(
						this.create_stacked_datasets(
							this.props.data.meanscore_global_values[0],
							first_index,
							getColors('meanscore_global_list', this.props.data.colors)[first_index],
							'Stack 2',
							15,
							true,
						),
					);
				}
			});
		}

		this.setState({
			options: options,
			data: data,
			dataIsSet: true,
		});
	}

	changeBenchmark() {
		var data = {
			labels: this.props.data.labels,
			datasets: [],
		};
		if (!this.props.data.selector) {
			this.props.data.values.map((values_list, first_index) => {
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.values,
						first_index,
						getColors(this.props.category + '_list', this.props.data.colors)[first_index],
						'Stack 0',
						25,
						this.state.activeBenchmark,
					),
				);
				if (this.props.data.meanscore_sector_values[first_index]) {
					data.datasets.push(
						this.create_stacked_datasets(
							this.props.data.meanscore_sector_values,
							first_index,
							getColors('meanscore_sector_list', this.props.data.colors)[first_index],
							'Stack 1',
							15,
							this.state.activeBenchmark,
						),
					);
				}
				if (this.props.data.meanscore_global_values[first_index]) {
					data.datasets.push(
						this.create_stacked_datasets(
							this.props.data.meanscore_global_values,
							first_index,
							getColors('meanscore_global_list', this.props.data.colors)[first_index],
							'Stack 2',
							15,
							this.state.activeBenchmark,
						),
					);
				}
			});
		} else {
			this.props.data.values[this.state.activeValues].map((values_list, first_index) => {
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.values[this.state.activeValues],
						first_index,
						getColors(this.props.category + '_list', this.props.data.colors)[first_index],
						'Stack 0',
						25,
						this.state.activeBenchmark,
					),
				);
				if (this.props.data.meanscore_sector_values[this.state.activeValues]) {
					data.datasets.push(
						this.create_stacked_datasets(
							this.props.data.meanscore_sector_values[this.state.activeValues],
							first_index,
							getColors('meanscore_sector_list', this.props.data.colors)[first_index],
							'Stack 1',
							15,
							this.state.activeBenchmark,
						),
					);
				}
				if (this.props.data.meanscore_global_values[this.state.activeValues]) {
					data.datasets.push(
						this.create_stacked_datasets(
							this.props.data.meanscore_global_values[this.state.activeValues],
							first_index,
							getColors('meanscore_global_list', this.props.data.colors)[first_index],
							'Stack 2',
							15,
							this.state.activeBenchmark,
						),
					);
				}
			});
		}

		this.setState({
			activeBenchmark: !this.state.activeBenchmark,
			data: data,
		});
	}

	changeDatas(e) {
		e.preventDefault();
		var data = {
			labels: this.props.data.labels,
			datasets: [],
		};

		this.props.data.values[e.target.value].map((values_list, first_index) => {
			data.datasets.push(
				this.create_stacked_datasets(
					this.props.data.values[e.target.value],
					first_index,
					getColors(this.props.category + '_list', this.props.data.colors)[first_index],
					'Stack 0',
					25,
					!this.state.activeBenchmark,
				),
			);
			if (this.props.data.meanscore_sector_values[e.target.value]) {
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.meanscore_sector_values[e.target.value],
						first_index,
						getColors('meanscore_sector_list', this.props.data.colors)[first_index],
						'Stack 1',
						15,
						!this.state.activeBenchmark,
					),
				);
			}
			if (this.props.data.meanscore_global_values[e.target.value]) {
				data.datasets.push(
					this.create_stacked_datasets(
						this.props.data.meanscore_global_values[e.target.value],
						first_index,
						getColors('meanscore_global_list', this.props.data.colors)[first_index],
						'Stack 2',
						15,
						!this.state.activeBenchmark,
					),
				);
			}
		});

		this.setState({
			data: data,
			activeValues: e.target.value,
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
				<div className="bar_container w-100" style={{ position: 'relative', height: '40vh' }}>
					{this.state.dataIsSet && (
						<React.Fragment>
							<Bar options={this.state.options} data={this.state.data} />
						</React.Fragment>
					)}
				</div>
				<div className="d-flex flex-column align-items-center">
					{this.state.dataIsSet && (
						<div className="circularChart_legend d-flex flex-column justify-content-center align-items-center flex-wrap mt-3">
							<div className="d-flex">
								<div className="legend_item p-2">{this.legendDescItem(getColors(this.props.category + '_list', [2]), gettext('Femmes'))}</div>
								<div className="legend_item p-2">{this.legendDescItem(getColors(this.props.category + '_list', [3]), gettext('Hommes'))}</div>
								{(this.props.data.selector && this.props.data.values[0].length === 3) ||
								(!this.props.data.selector && this.props.data.values.length === 3) ? (
									<div className="legend_item p-2">
										{this.legendDescItem(getColors(this.props.category + '_list', [5]), gettext('Personnes Non-binaires'))}
									</div>
								) : (
									''
								)}
								{this.state.activeBenchmark === true ? (
									<div className="legend_item p-2">{this.legendDescItem(getColors('meanscore_sector', [1]), gettext('Moyenne Secteur'))}</div>
								) : (
									''
								)}
								{this.state.activeBenchmark === true ? (
									<div className="legend_item p-2">{this.legendDescItem(getColors('meanscore_global', [1]), gettext('Moyenne Globale'))}</div>
								) : (
									''
								)}
							</div>
						</div>
					)}
					{this.state.dataIsSet && this.props.data.meanscore_global_values[0] && (
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

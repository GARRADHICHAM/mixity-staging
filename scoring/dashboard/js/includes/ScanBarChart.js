import React, { Component } from 'react';
import ChartDataLabels from 'chartjs-plugin-datalabels';

import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { getColors, dataLabelColor } from './ColorData';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ChartDataLabels);

export default class ScanBarChart extends Component {
	constructor(props) {
		super(props);
		this.state = {
			options: {},
			data: {},
			dataIsSet: false,
			activeIndex: 0,
			specialLabel: false,
			activeBenchmark: false,
		};
	}

	create_basic_datasets(label, values, activeIndex, bgColors, order, benchmark) {
		return {
			label: label,
			data: this.props.data.selector && activeIndex !== 0 ? values[activeIndex][order] : values[activeIndex],
			backgroundColor: bgColors,
			borderWidth: 0,
			borderRadius: 100,
			hidden: benchmark,
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
					return '';
				},
				textAlign: 'center',
			},
		};
	}

	legendDescItem(color, text, isEntity = false) {
		return (
			<div className="d-inline-flex align-items-center py-2">
				<div>
					<div className="indic-score" style={{ backgroundColor: `${color}` }}></div>
				</div>
				{isEntity ? <span className="legend_value fw-bold">{text}</span> :
					<span className="legend_value">{text}</span>}
			</div>
		);
	}

	componentDidMount() {
		//Defining Bar options
		var options = {
			scales: {
				y: {
					display: true,
					border: {
						display: true,
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
					stacked: false,
					border: {
						display: true,
						color: '#E6E8EC',
					},
					grid: {
						display: true,
					},
					ticks: {
						callback: function(value, index, values) {
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
				title: {
					display: false,
				},
			},
		};

		var special_label_case = false;
		var data = {
			labels: [gettext("Bonne réponse"), gettext("Partiellement correct"), gettext("Mauvaise réponse")],
			datasets: [
				this.create_basic_datasets(gettext('Entreprise'), this.props.data.values, 0, getColors(this.props.category, [3]),  0, false),
				this.create_basic_datasets(gettext('Secteur'), this.props.data.meanscore_sector_values, 0, getColors('meanscore_sector', [1]),  1, true),
				this.create_basic_datasets(gettext('Global'), this.props.data.meanscore_global_values, 0, getColors('meanscore_global', [1]), 2, true),
			]
		};

		this.setState({
			options: options,
			data: data,
			dataIsSet: true,
			specialLabel: special_label_case,
		});
	}

	changeDatas(e) {
		e.preventDefault();
		if (!this.props.data.selector)
			return
		this.setState({
			activeBenchmark: false,
		});
		var value = parseInt(e.target.value, 10)
		var datasets = []
		if (value === 0) {
			datasets = [
				this.create_basic_datasets('Entreprise', this.props.data.values, value, getColors(this.props.category, [3]),  0, false),
				this.create_basic_datasets('Secteur', this.props.data.meanscore_sector_values, value, getColors('meanscore_sector', [1]),  1, true),
				this.create_basic_datasets('Global', this.props.data.meanscore_global_values, value, getColors('meanscore_global', [1]), 2, true),
			]
		} else {
			this.props.data.labels.map((label, index) => (
				datasets.push(this.create_basic_datasets(label, this.props.data.values, value, getColors(this.props.category + '_list', [index + 1]),  index, false),)
			))
		}
		var data = {
			labels: [gettext("Bonne réponse"), gettext("Partiellement correct"), gettext("Mauvaise réponse")],
			datasets: datasets
		};

		this.setState({
			data: data,
			activeIndex: value,
		});
	}

	changeBenchmark() {
		var data = {
			labels: [gettext("Bonne réponse"), gettext("Partiellement correct"), gettext("Mauvaise réponse")],
			datasets: [
				this.create_basic_datasets(
					'Entreprise',
					this.props.data.values,
					this.state.activeIndex,
					getColors(this.props.category, [3]),
					0,
					false,
				),
				this.create_basic_datasets(
					'Secteur',
					this.props.data.meanscore_sector_values,
					this.state.activeIndex,
					getColors('meanscore_sector', [1]),
					1,
					this.state.activeBenchmark,
				),
				this.create_basic_datasets(
					'Global',
					this.props.data.meanscore_global_values,
					this.state.activeIndex,
					getColors('meanscore_global', [1]),
					2,
					this.state.activeBenchmark,
				),
			],
		};

		this.setState({
			activeBenchmark: !this.state.activeBenchmark,
			data: data,
		});
	}

	render() {
		return (
			<React.Fragment>
				{this.props.data.selector && (
					<select className="select_indicator mb-5" name="selectedSubquestion" defaultValue="0"
							onChange={(e) => this.changeDatas(e)}>
						{this.props.data.selector_labels.map((label, index) => {
							return (
								<option key={index} value={index}>
									{label}
								</option>
							);
						})}
					</select>
				)}
				<div
					className="bar_container w-100"
					style={{
						position: 'relative',
						height: '48vh',
					}}
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
				<div className="d-flex flex-column align-items-center w-100 pb-3">
					<div className="w-100 text-center py-2 d-flex justify-content-around"
						 style={{ paddingLeft: '0.8vw', paddingRight: '0.8vw' }}>
						{[gettext("Bonne réponse"), gettext("Partiellement correct"), gettext("Mauvaise réponse")].map((label, index) => {
							return (
								<h6 key={index} style={{ fontSize: '12px' }}>{label}</h6>
							);
						})}
					</div>
					{this.state.activeIndex <= 0 ? (
						<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap my-3">
							<div className="legend_item">
								{this.legendDescItem(
									getColors(this.props.category, [1]),
									gettext('Entreprise'),
									true
								)}
							</div>
							{this.state.activeBenchmark && (
								<>
									<div className="legend_item px-2">
										{this.legendDescItem(
											getColors('meanscore_sector', [1]),
											gettext('Moyenne Secteur'),
											false,
										)}
									</div>
									<div className="legend_item">
										{this.legendDescItem(
											getColors('meanscore_global', [1]),
											gettext('Moyenne Globale'),
											false,
										)}
									</div>
								</>
							)}
						</div>
					) : (
						<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap my-3">
							{this.props.data.labels.map((label, index) => {
								return (
									<div className="legend_item me-2">{this.legendDescItem(getColors(this.props.category + '_list', [index + 1]), label, false)}</div>
								)
							})}
						</div>
					)}
					{this.state.dataIsSet && this.state.activeIndex === 0 && this.props.data.display_params.stacked === false && (
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

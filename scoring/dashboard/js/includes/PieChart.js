import React, { Component } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { getColors, dataLabelColor } from './ColorData';

ChartJS.register(ArcElement, Tooltip, Legend, ChartDataLabels);

export default class PieChart extends Component {
	constructor(props) {
		super(props);
		this.state = {
			options: {},
			data: {},
			global_data: {},
			sector_data: {},
			activeIndex: 0,
			activeBenchmark: false,
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

	componentDidMount() {
		if (this.props.data.selector ? this.props.data.labels[0].length === 6 : this.props.data.labels.length === 6) {
			this.props.data.colors.push(3);
		}
		let delayed;
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
					display: false,
					text: this.props.data.title,
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
						return Math.round(value) > 6 ? `${Math.round(value)}%` : '';
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
		var data = {
			labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
			datasets: [
				{
					label: '',
					data: this.props.data.selector ? this.props.data.values[0] : this.props.data.values,
					backgroundColor: getColors(this.props.category + '_list', this.props.data.colors),
				},
			],
		};
		var global_data = {
			labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
			datasets: [
				{
					label: '',
					data: this.props.data.selector ? this.props.data.meanscore_global_values[0] : this.props.data.meanscore_global_values,
					backgroundColor: getColors('meanscore_global_list', this.props.data.colors),
				},
			],
		};
		var sector_data = {
			labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
			datasets: [
				{
					label: '',
					data: this.props.data.selector ? this.props.data.meanscore_sector_values[0] : this.props.data.meanscore_sector_values,
					backgroundColor: getColors('meanscore_sector_list', this.props.data.colors),
				},
			],
		};

		this.setState({
			options: options,
			data: data,
			global_data: global_data,
			sector_data: sector_data,
		});
	}

	changeDatas(e) {
		e.preventDefault();
		var data = {
			labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
			datasets: [
				{
					label: '',
					data: this.props.data.values[e.target.value],
					backgroundColor: getColors(this.props.category + '_list', this.props.data.colors),
				},
			],
		};
		var global_data = {
			labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
			datasets: [
				{
					label: '',
					data: this.props.data.meanscore_global_values[e.target.value],
					backgroundColor: getColors('meanscore_global_list', this.props.data.colors),
				},
			],
		};
		var sector_data = {
			labels: this.props.data.selector ? this.props.data.labels[0] : this.props.data.labels,
			datasets: [
				{
					label: '',
					data: this.props.data.meanscore_sector_values[e.target.value],
					backgroundColor: getColors('meanscore_sector_list', this.props.data.colors),
				},
			],
		};
		this.setState({
			data: data,
			global_data: global_data,
			sector_data: sector_data,
			activeIndex: e.target.value,
		});
	}

	render() {
		return (
			<React.Fragment>
				{this.state.data.labels && (
					<div className="pie_indicator_container w-100 d-flex flex-column align-items-center">
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
						<div className="w-100" style={{ position: 'relative', height: `${this.props.isCriteria ? '15vh' : '30vh'}` }}>
							<div className="d-flex justify-content-between">
								<div
									className={`pie_container ${!this.props.isCriteria && this.state.activeBenchmark ? 'w-50' : 'w-100'}`}
									style={{ position: 'relative', height: `${this.props.isCriteria ? '15vh' : '30vh'}` }}
								>
									{this.state.data.datasets[0].data.length === 0 ? (
										<div className="d-flex justify-content-center align-items-center">
											<b style={{ fontSize: '24px' }}>No data available</b>
										</div>
									) : (
										<Pie data={this.state.data} options={this.state.options} />
									)}
								</div>
								{!this.props.isCriteria && this.state.activeBenchmark && (
									<div className="pie_container w-50 align-content-between" style={{ height: '14vh' }}>
										{this.state.sector_data.datasets[0].data.length === 0 ? (
											<div className="d-flex justify-content-center align-items-center">
												<b style={{ fontSize: '24px' }}>No data available</b>
											</div>
										) : (
											<Pie data={this.state.sector_data} options={this.state.options} />
										)}
										<br />
										{this.state.global_data.datasets[0].data.length === 0 ? (
											<div className="d-flex justify-content-center align-items-center">
												<b style={{ fontSize: '24px' }}>No data available</b>
											</div>
										) : (
											<Pie data={this.state.global_data} options={this.state.options} />
										)}
									</div>
								)}
							</div>
						</div>
						<div className="circularChart_legend d-flex justify-content-evenly align-items-center flex-wrap my-3 py-3">
							{this.props.data.selector
								? this.props.data.labels[this.state.activeIndex].map((label, index) => {
										return (
											<div key={index} className="d-inline-flex align-items-center py-2 pe-3">
												<div>
													<div
														className="indic-score"
														style={{
															backgroundColor: `${getColors(this.props.category + '_list', [this.props.data.colors[index]])[0]}`,
														}}
													></div>
												</div>
												<span className="legend_value">{label}</span>
											</div>
										);
								  })
								: this.props.data.labels.map((label, index) => {
										return (
											<div key={index} className="d-inline-flex align-items-center py-2 pe-3">
												<div>
													<div
														className="indic-score"
														style={{
															backgroundColor: `${getColors(this.props.category + '_list', [this.props.data.colors[index]])[0]}`,
														}}
													></div>
												</div>
												<span className="legend_value">{label}</span>
											</div>
										);
								  })}
						</div>
						{this.state.activeBenchmark && (
							<div className="d-flex">
								<div className="legend_item px-2">{this.legendDescItem(getColors('meanscore_sector', [1]), gettext('Moyenne Secteur'))}</div>
								<div className="legend_item px-2">{this.legendDescItem(getColors('meanscore_global', [1]), gettext('Moyenne Globale'))}</div>
							</div>
						)}
						{!this.props.isCriteria && (
							<React.Fragment>
								<div className="d-flex gap-2 justify-content-center align-items-center my-3">
									<div className="d-flex align-items-center">
										<input
											type="checkbox"
											id={`input-filter-${this.props.data.title}`}
											value={this.state.activeBenchmark}
											onClick={() => this.setState({ activeBenchmark: !this.state.activeBenchmark })}
										></input>
										<label className="ps-2">{gettext('Afficher le Benchmark')}</label>
									</div>
								</div>
							</React.Fragment>
						)}
					</div>
				)}
			</React.Fragment>
		);
	}
}

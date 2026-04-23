import React from 'react';
import { CircularProgressbarWithChildren, buildStyles } from 'react-circular-progressbar';
import { Card } from 'react-bootstrap';
import { getColors } from './ColorData';

export default class ScanCircularChart extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			alpha: [0.3, 0.6, 1],
			activeIndex: 0,
			activeBenchmark: false,
		};
	}

	legendDescItem(color, text, isEntity = false, value) {
		return (
			<div className="d-inline-flex align-items-center py-2">
				<div>
					<div className="indic-score" style={{ backgroundColor: `${color}` }}></div>
				</div>
				{isEntity ? (
					<span className="legend_value fw-bold">{text}</span>
				) : (
					<span className="legend_value">
						{text} : {value}
					</span>
				)}
			</div>
		);
	}

	handleChange = (value) => {
		this.setState({
			activeBenchmark: false,
			activeIndex: parseInt(value, 10),
		})
	};

	convertToRGB(hexa, alpha) {
		hexa = hexa.slice(1);
		if (hexa.length != 6) {
			return 'rgba(255, 255, 255, 0.1)';
		}

		var aRgbHex = hexa.match(/.{1,2}/g);
		var aRgb = `rgba(${parseInt(aRgbHex[0], 16)},${parseInt(aRgbHex[1], 16)},${parseInt(aRgbHex[2], 16)},${alpha})`;
		return aRgb;
	}

	valueorND(values) {
		if (this.props.data.selector && values[this.state.activeIndex].length > 0) {
			if (values[this.state.activeIndex][0] > 10) return Math.round(values[this.state.activeIndex][0]) + ' %';
			else return values[this.state.activeIndex][0] + ' %';
		} else if (!this.props.data.selector && values.length > 0) {
			if (Math.round(values[0]) > 10) return Math.round(Math.round(values[0])) + ' %';
			else return values[0] + ' %';
		} else return gettext("Cette donnée n'est pas disponible");
	}

	pathLength(values) {
		if (this.props.data.selector && values[this.state.activeIndex][0]) return Math.round(values[this.state.activeIndex][0]);
		else if (!this.props.data.selector && values[0]) return Math.round(values[0]);
		else return 0;
	}

	circularChartByJobs = (index) => {
		if (!this.props.data.selector) return;
		return (
			<CircularProgressbarWithChildren
				key={`circularJob-${index}`}
				value={Math.round(this.props.data.values[1][index])}
				strokeWidth={index < 4 ? 3 : 8}
				styles={buildStyles({
					rotation: 0.5,
					strokeLinecap: 'round',
					pathColor: getColors(this.props.category + '_list', [5 - index]),
					trailColor: 'rgba(240, 243, 255, 1)',
				})}
			>
				{index < 4 ? (
					<div className="score__stroke">{this.circularChartByJobs(index + 1)}</div>
				) : (
					<Card.Text className="score__percentage m-0" style={{ fontSize: '1.5rem', color: getColors(this.props.category + '_secondary', [1]) }}>
						<b>{Math.round(this.props.data.values[1][index])}</b>
					</Card.Text>
				)}
			</CircularProgressbarWithChildren>
		);
	};

	render() {
		return (
			<React.Fragment>
				<h4 className="w-100 fw-medium text-center mb-4" style={{ fontWeight: '400', fontSize: '14px' }}>
					{gettext('Taux de bonnes réponses')}
				</h4>
				{this.props.data.selector && (
					<select className="select_indicator mb-3" name="selectedSubquestion" defaultValue="0"
							onChange={(e) => this.handleChange(e.target.value)}>
						{this.props.data.selector_labels.map((label, index) => {
							return (
								<option key={index} value={`${index}`}>
									{label}
								</option>
							);
						})}
					</select>
				)}
				<div className="circular_container w-50">
					<div className="px-0 py-2 text-center">
						{this.state.activeIndex === 0 ? (
							<CircularProgressbarWithChildren
								key="CircularMain"
								value={this.pathLength(this.props.data.meanscore_global_values)}
								strokeWidth={3}
								styles={buildStyles({
									rotation: 0.5,
									strokeLinecap: 'round',
									pathColor: this.state.activeBenchmark === true ? getColors('meanscore_global', [1]) : '#fff',
									trailColor: this.state.activeBenchmark === true ? 'rgba(240, 243, 255, 1)' : '#fff',
								})}
							>
								<div className="score__stroke">
									<CircularProgressbarWithChildren
										value={this.pathLength(this.props.data.meanscore_sector_values)}
										strokeWidth={3}
										styles={buildStyles({
											rotation: 0.5,
											strokeLinecap: 'round',
											pathColor: this.state.activeBenchmark === true ? getColors('meanscore_sector', [1]) : '#fff',
											trailColor: this.state.activeBenchmark === true ? 'rgba(240, 243, 255, 1)' : '#fff',
										})}
									>
										<div className="score__stroke">
											<CircularProgressbarWithChildren
												value={this.pathLength(this.props.data.values)}
												strokeWidth={8}
												styles={buildStyles({
													rotation: 0.5,
													strokeLinecap: 'round',
													pathColor: getColors(this.props.category, [1]),
													trailColor: 'rgba(240, 243, 255, 1)',
												})}
											>
												<Card.Text
													className="score__percentage m-0"
													style={{ fontSize: '1.5rem', color: getColors(this.props.category, [1]) }}
												>
													<b>{this.valueorND(this.props.data.values)}</b>
												</Card.Text>
											</CircularProgressbarWithChildren>
										</div>
									</CircularProgressbarWithChildren>
								</div>
							</CircularProgressbarWithChildren>
						) : (
							<div key={0}>{this.circularChartByJobs(0)}</div>
						)}
					</div>
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
										this.valueorND(this.props.data.meanscore_sector_values),
									)}
								</div>
								<div className="legend_item">
									{this.legendDescItem(
										getColors('meanscore_global', [1]),
										gettext('Moyenne Globale'),
										false,
										this.valueorND(this.props.data.meanscore_global_values),
									)}
								</div>
							</>
						)}
					</div>
				) : (
					<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap my-3">
						{this.props.data.labels.map((label, index) => {
							return (
								<div className="legend_item me-2">
									{this.legendDescItem(
										getColors(this.props.category + '_list', [index + 1]),
										label,
										false,
										this.props.data.values[1][4 - index] + '%',
									)}
								</div>
							);
						})}
					</div>
				)}
				{this.state.activeIndex === 0 && (
					<React.Fragment>
						<div className="d-flex gap-2 justify-content-center align-items-center my-3">
							<div className="d-flex align-items-center">
								<input
									type="checkbox"
									id={`input-filter-${this.props.title}`}
									value={this.state.activeBenchmark}
									onClick={() => this.setState({ activeBenchmark: !this.state.activeBenchmark })}
									></input>
								<label className="ps-2">{gettext('Afficher le Benchmark')}</label>
							</div>
						</div>
					</React.Fragment>
				)}
			</React.Fragment>
		);
	}
}

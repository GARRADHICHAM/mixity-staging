import React from 'react';
import { CircularProgressbarWithChildren, buildStyles } from 'react-circular-progressbar';
import { Card } from 'react-bootstrap';
import { getColors } from './ColorData';

export default class CircularChart extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			alpha: [0.3, 0.6, 1],
			activeIndex: 0,
			activeBenchmark: false,
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
		if (values.length === 0)
			return gettext("Cette donnée n'est pas disponible");
		if (this.props.data.selector && values[this.state.activeIndex].length > 0) {
			if (values[this.state.activeIndex][0] > 10)
				return Math.round(values[this.state.activeIndex][0]) + ' %';
			else
				return values[this.state.activeIndex][0] + ' %';
		} else if (!this.props.data.selector && values.length > 0) {
			if (Math.round(values[0]) > 10)
				return Math.round(Math.round(values[0])) + ' %';
			else
				return values[0] + ' %';
		} else
			return gettext("Cette donnée n'est pas disponible");
	}

	pathLength(values) {
		var value = 0;
		if (values.length === 0)
			return 0
		if (this.props.data.selector && values[this.state.activeIndex][0])
			value = values[this.state.activeIndex][0];
		else if (!this.props.data.selector && values[0])
			value = values[0];
		return value;
	}

	render() {
		return (
			<React.Fragment>
				{this.props.data.selector && (
					<select
						className="select_indicator mb-3"
						name="selectedSubquestion"
						defaultValue="0"
						onChange={(e) => this.setState({ activeIndex: e.target.value })}
					>
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
				<div className="circular_container w-50">
					<div className="px-0 py-2 text-center">
						<CircularProgressbarWithChildren
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
					</div>
				</div>
				{this.state.activeBenchmark === true && (
					<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap my-3">
						<div className="d-inline-flex align-items-center py-2 me-2">
							<div>
								<div className="indic-score" style={{ backgroundColor: `${getColors('meanscore_global', [1])}` }}></div>
							</div>
							{
								<span className="legend_value fw-bold" style={{ color: `${getColors('meanscore_global', [1])}` }}>
									{this.valueorND(this.props.data.meanscore_global_values)}
								</span>
							}
						</div>
						<div className="d-inline-flex align-items-center py-2">
							<div>
								<div className="indic-score" style={{ backgroundColor: `${getColors('meanscore_sector', [1])}` }}></div>
							</div>
							{
								<span className="legend_value fw-bold" style={{ color: `${getColors('meanscore_sector', [1])}` }}>
									{this.valueorND(this.props.data.meanscore_sector_values)}
								</span>
							}
						</div>
					</div>
				)}
				<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap my-3">
					<div className="legend_item">{this.legendDescItem(getColors(this.props.category, [1]), gettext('Entreprise'), true)}</div>
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
			</React.Fragment>
		);
	}
}

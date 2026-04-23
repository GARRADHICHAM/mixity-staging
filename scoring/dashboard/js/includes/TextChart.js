import React, { Component } from 'react';
import { getColors } from './ColorData';

export default class TextChart extends Component {
	constructor(props) {
		super(props);
		this.state = {
			activeBenchmark: false,
			activeIndex: 0,
		};
	}

	legendDescItem(color, value) {
		return (
			<div className="d-inline-flex align-items-center py-2">
				<div>
					<div className="indic-score" style={{ backgroundColor: `${color}` }}></div>
				</div>
				<span className="legend_value" style={{ fontSize: '1rem' }}>
					{value}
				</span>
			</div>
		);
	}

	valueorND(values) {
		if (this.props.data.id === 20236001)
			return values[0];
		else if (this.props.data.selector && values[this.state.activeIndex].length > 0) {
			if (values[this.state.activeIndex][0] > 10)
				return Math.round(values[this.state.activeIndex][0]);
			else
				return values[this.state.activeIndex][0];
		} else if (!this.props.data.selector && values.length > 0) {
			if (values[0] > 10)
				return Math.round(values[0]);
			else
				return values[0];
		} else
			return gettext("Cette donnée n'est pas disponible");
	}

	render() {
		return (
			<React.Fragment>
				<div className="textIndicator_container d-flex flex-column">
					<h3 className="fw-medium mb-3">{this.props.data.title}</h3>
					<div className="d-flex align-items-center">
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
					</div>
					<div className="d-flex align-items-center" style={{ width: 'fit-content', fontSize: '2rem' }}>
						<span class="fw-bold">{this.valueorND(this.props.data.values)}</span>
						<span class="fw-bold">
							{this.valueorND(this.props.data.values) !== gettext("Cette donnée n'est pas disponible") && this.props.data.display_params.ending}
						</span>
						{this.state.activeBenchmark && (
							<React.Fragment>
								<b>
									<p className="ps-4 pe-3" style={{ fontSize: '1rem', color: `${getColors('meanscore_sector', [1])}` }}>
										{this.valueorND(this.props.data.meanscore_sector_values)}
									</p>
								</b>
								<b>
									<p style={{ fontSize: '1rem', color: `${getColors('meanscore_global', [1])}` }}>
										{this.valueorND(this.props.data.meanscore_global_values)}
									</p>
								</b>
							</React.Fragment>
						)}
					</div>
					<React.Fragment>
						<div className="d-flex">
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
					</React.Fragment>
					{this.props.data.id === 20236001 ? (
						''
					) : (
						<div className="d-flex justify-content-between align-items-end my-3">
							<React.Fragment>
								<div className="d-flex align-items-center ps-1">
									<input
										type="checkbox"
										id={`input-filter-${this.props.title}`}
										value={this.state.activeBenchmark}
										onClick={() => this.setState({ activeBenchmark: !this.state.activeBenchmark })}
									></input>
									<label className="ps-2">{gettext('Afficher le Benchmark')}</label>
								</div>
							</React.Fragment>
						</div>
					)}
					{this.props.svg && (
						<div className="d-flex justify-content-between align-items-end my-3">
							<div></div>
							<div style={{ width: '20%' }}>
								<img src={'/static/img/textChart/' + this.props.svg} />
							</div>
						</div>
					)}
				</div>
			</React.Fragment>
		);
	}
}

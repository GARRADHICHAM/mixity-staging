import React from 'react';
import { Card } from 'react-bootstrap';
import { CircularProgressbar, CircularProgressbarWithChildren, buildStyles } from 'react-circular-progressbar';
import { getColors } from '../../../scoring/dashboard/js/includes/ColorData';

export default class CircularChart extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			alpha: [0.3, 0.6, 1],
		};
	}

	componentDidMount() {}

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

	pathLength(values) {
		if (this.props.data.selector && values[this.state.activeIndex][0])
			return values[this.state.activeIndex][0];
		else if (!this.props.data.selector && values[0])
			return values[0];
		return 0;
	}

	render() {
		return (
			<React.Fragment>
				<div className="circular_container w-50">
					<div className="px-0 py-2 text-center">
						<CircularProgressbarWithChildren
							value={this.pathLength(this.props.data[0])}
							strokeWidth={3}
							styles={buildStyles({
								rotation: 0.5,
								strokeLinecap: 'round',
								pathColor: this.convertToRGB(this.props.color, this.state.alpha[0]),
								// pathColor: this.state.activeBenchmark === true ? getColors("meanscore_sector", [1]) : "#fff",
								// trailColor: this.state.activeBenchmark === true ? "rgba(240, 243, 255, 1)" : "#fff",
							})}
						>
							<div className="score__stroke">
								<CircularProgressbarWithChildren
									value={this.pathLength(this.props.data[1])}
									strokeWidth={3}
									styles={buildStyles({
										rotation: 0.5,
										strokeLinecap: 'round',
										pathColor: this.convertToRGB(this.props.color, this.state.alpha[1]),
										// pathColor: this.state.activeBenchmark === true ? getColors("meanscore_global", [1]) : "#fff",
										// trailColor: this.state.activeBenchmark === true ? "rgba(240, 243, 255, 1)" : "#fff",
									})}
								>
									<div className="score__stroke">
										<CircularProgressbarWithChildren
											value={this.pathLength(this.props.data[2])}
											strokeWidth={8}
											styles={buildStyles({
												rotation: 0.5,
												strokeLinecap: 'round',
												pathColor: getColors('all', [1]),
												trailColor: 'rgba(240, 243, 240, 1)',
											})}
										>
											<Card.Text className="score__percentage m-0" style={{ fontSize: '1.5rem', color: getColors('all', [1]) }}>
												<b>{Math.round(this.props.data[2])}%</b>
											</Card.Text>
										</CircularProgressbarWithChildren>
									</div>
								</CircularProgressbarWithChildren>
							</div>
						</CircularProgressbarWithChildren>
					</div>
				</div>
				{/* {this.state.activeBenchmark === true &&
          <div className='circularChart_legend d-flex justify-content-center align-items-center flex-wrap my-3'>
            <div className="d-inline-flex align-items-center py-2 me-2">
                <div><div className="indic-score" style={{ backgroundColor: `${getColors("meanscore_sector", [1])}` }}></div></div>
                {<span className='legend_value fw-bold' style={{ color: `${getColors("meanscore_sector", [1])}` }}>{this.valueorND(this.props.data.meanscore_sector_values) + " %"}</span>}
            </div>
            <div className="d-inline-flex align-items-center py-2">
                <div><div className="indic-score" style={{ backgroundColor: `${getColors("meanscore_global", [1])}` }}></div></div>
                {<span className='legend_value fw-bold' style={{ color: `${getColors("meanscore_global", [1])}` }}>{this.valueorND(this.props.data.meanscore_global_values) + " %"}</span>}
            </div>
          </div>
        } */}
				<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap my-3">
					<div className="legend_item">{this.legendDescItem(getColors('all', [1]), gettext('Entreprise'), true)}</div>
					{/* {this.state.activeBenchmark === true ? <div className='legend_item px-2'>{this.legendDescItem(getColors("meanscore_sector", [1]), gettext("Moyenne Secteur"))}</div> : ""}
          {this.state.activeBenchmark === true ?<div className='legend_item'>{this.legendDescItem(getColors("meanscore_global", [1]), gettext("Moyenne Globale"))}</div> : ""} */}
				</div>
				{/* <React.Fragment>
          <div className="d-flex gap-2 justify-content-center align-items-center my-3">
            <div className="d-flex align-items-center">
              <input type="checkbox" id={`input-filter-${this.props.title}`} value={this.state.activeBenchmark} onClick={() => this.setState({activeBenchmark:!this.state.activeBenchmark})}></input>
              <label className="ps-2">{gettext("Afficher le Benchmark")}</label>
            </div>
          </div>
        </React.Fragment> */}
			</React.Fragment>
		);
	}
}

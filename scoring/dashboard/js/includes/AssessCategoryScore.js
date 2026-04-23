import React, { Component } from 'react';
import { CircularProgressbar, CircularProgressbarWithChildren, buildStyles } from 'react-circular-progressbar';
import { getColors } from './ColorData';

class AssessCategoryScore extends Component {
	constructor(props) {
		super(props);
	}

	render() {
		return (
			<div className="d-flex column-flex flex-wrap" style={{ width: '100%' }}>
				{/* Outter score circular progress bars */}
				<div className="w-100">
					<CircularProgressbarWithChildren
						value={this.props.outterPercent}
						strokeWidth={3}
						counterClockwise={true}
						styles={buildStyles({
							pathColor: getColors('meanscore_global', [1]),
							strokeLinecap: 'round',
							trailColor: '#F0F3FF',
						})}
					>
						{/* Score comparing to all the structures circular progress bars */}
						<div style={{ width: '84%' }}>
							<CircularProgressbarWithChildren
								value={this.props.betweenPercent}
								strokeWidth={3}
								counterClockwise={true}
								styles={buildStyles({
									pathColor: getColors('meanscore_sector', [1]),
									strokeLinecap: 'round',
									trailColor: '#F0F3FF',
								})}
							>
								<div style={{ width: '80%' }}>
									<CircularProgressbarWithChildren
										value={this.props.innerPercent}
										strokeWidth={7}
										counterClockwise={true}
										styles={buildStyles({
											pathColor: this.props.innerColor,
											strokeLinecap: 'round',
											trailColor: '#F0F3FF',
										})}
									>
										<span className="fw-bold" style={{ fontSize: '1.5rem' }}>{`${this.props.innerPercent}%`}</span>
									</CircularProgressbarWithChildren>
								</div>
							</CircularProgressbarWithChildren>
						</div>
					</CircularProgressbarWithChildren>
				</div>
				{/*  Remaining scores description  */}
				<div className="d-flex row-flex justify-content-between align-items-center mt-4" style={{ width: '100%' }}>
					<div className="d-flex row-flex" style={{ width: '50%' }}>
						<div style={{ width: '20%', marginRight: '.5rem' }}>
							<CircularProgressbar value={10} background styles={buildStyles({ backgroundColor: getColors('meanscore_global', [1]) })} />
						</div>
						<span className="fw-bold">
							{this.props.outterPercent}
							<span>%</span>
						</span>
					</div>
					<div className="d-flex row-flex justify-content-end" style={{ width: '50%' }}>
						<div style={{ width: '20%', marginRight: '.5rem' }}>
							<CircularProgressbar value={10} background styles={buildStyles({ backgroundColor: getColors('meanscore_sector', [1]) })} />
						</div>
						<span className="fw-bold">
							{this.props.betweenPercent}
							<span>%</span>
						</span>
					</div>
				</div>
			</div>
		);
	}
}

export default AssessCategoryScore;

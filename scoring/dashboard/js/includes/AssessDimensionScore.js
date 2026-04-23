import React, { Component } from 'react';
import { CircularProgressbar, CircularProgressbarWithChildren, buildStyles } from 'react-circular-progressbar';

class AssessDimensionScore extends Component {
	constructor(props) {
		super(props);
	}

	render() {
		return (
			<div className="w-100">
				{/* score circular progress bars */}
				<div className="m-0" style={{ width: '80%' }}>
					<CircularProgressbarWithChildren
						value={this.props.dimensionPercent}
						strokeWidth={8}
						counterClockwise={true}
						styles={buildStyles({
							pathColor: this.props.dimensionColor,
							strokeLinecap: 'round',
							trailColor: '#F0F3FF',
						})}
					>
						<span className="fw-bold" style={{ fontSize: '1rem' }}>{`${this.props.dimensionPercent}%`}</span>
					</CircularProgressbarWithChildren>
				</div>
			</div>
		);
	}
}

export default AssessDimensionScore;

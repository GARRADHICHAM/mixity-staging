import React, { Component } from 'react';
import { Skeleton } from '@mui/material';

class AssessSubCategoryScoreSkeletonLoader extends Component {
	constructor(props) {
		super(props);
	}

	render() {
		let skeletonsCount = this.props.skeletonsCount;
		let skeletons = [];
		for (let i = 0; i < skeletonsCount; i++) {
			skeletons.push(
				<div className="d-flex flex-column" key={i} style={{ width: '26%' }}>
					<Skeleton variant="circular" width={104} height={104} />
					<Skeleton variant="text" width={104} />
				</div>,
			);
		}
		return (
			<div id="assess_global_scores_subcategories_skeleton" className="assess_global_scores_subcategories">
				{skeletons}
			</div>
		);
	}
}

export default AssessSubCategoryScoreSkeletonLoader;

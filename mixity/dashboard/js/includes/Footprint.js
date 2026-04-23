import React from 'react';
import RadialChart from '../../../../theme/src/js/RadialChart';
import * as d3 from 'd3';
import RadialGenreChart from '../../../../theme/src/js/RadialGenreChart';
import { calculateOffset } from '../../../../theme/src/js/Radar';

export default class Footprint extends React.Component {
	constructor(props) {
		super(props);
		this.myReference = React.createRef();
	}

	componentDidMount() {
		this.update();
	}

	update() {
		var data = this.props.data;
		let isCategoryEvaluation = data.isCategoryEvaluation;

		if (typeof data.measures === 'string') {
			data.measures = data.measures.replace(/'/g, '"');
			data.measures = JSON.parse(data.measures);
			}
		// const size =document.getElementById(data.id).offsetWidth
		const { width, height } = calculateOffset(data.id);
		const svg = d3
			.select(document.getElementById(data.id))
			.append('svg')
			.attr('id', `svg_${this.myReference.current.id}`)
			.attr('width', width)
			.attr('height', height);
		let chart = null;
		if (!isCategoryEvaluation) {
			chart = new RadialChart(`svg_${this.myReference.current.id}`);
		} else {
			chart = new RadialGenreChart(`svg_${this.myReference.current.id}`);
		}
		chart.initData(
			data.measures,
			{ enableInteraction: true, mirrorsvg: data.mirror, enableLegend: data.enableLegend, disableLegend: true, enableLinks: data.enableLinks },
			data.horizontal,
		);
		let previousSize = 0;
		// function resize(reference, isCategoryEvaluation){
		//     console.log("......Resizing")
		//
		//     // if (data.horizontal){
		//     //     console.log("Resizing should be different HERE 1")
		//     //     const { width, height } = calculateOffset(data.id,data.horizontal)
		//     //     if(width !== previousSize || height !== previousSize) {
		//     //         svg.attr('width', width).attr('height', height)
		//     //         chart.rerender(data.horizontal)
		//     //     }
		//     // }else{
		//     //     console.log("Resizing should be different HERE 2")
		//     //     const size = document.getElementById(data.id).offsetWidth;
		//     //     if (size !== previousSize) {
		//     //         svg.attr('width', size).attr('height', size)
		//     //         chart.rerender()
		//     //     }
		//     // }
		// }
		// document.addEventListener('resize', resize)
		// setInterval(resize, 500)
		// document.addEventListener('resize', () => { resize(this.myReference, isCategoryEvaluation); })
		// setInterval(() => { resize(this.myReference, isCategoryEvaluation); }, 500)
	}

	render() {
		return (
			<div
				className={'d-flex justify-content-center radar'}
				ref={this.myReference}
				id={this.props.data.id}
				style={this.props.data.isHomePage === true ? { width: '100%' } : { width: '47%' }}
			></div>
		);
	}
}

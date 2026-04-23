/* global d3 */
import concat from 'lodash-es/concat';
import uniq from 'lodash-es/uniq';
import flatten from 'lodash-es/flatten';
import max from 'lodash-es/max';
import groupBy from 'lodash-es/groupBy';

// Polyfill for .fill(
if (!Array.prototype.fill) {
	Object.defineProperty(Array.prototype, 'fill', {
		value: function (value) {
			// Steps 1-2.
			if (this == null) {
				throw new TypeError('this is null or not defined');
			}
			var O = Object(this);
			// Steps 3-5.
			var len = O.length >>> 0;
			// Steps 6-7.
			var start = arguments[1];
			var relativeStart = start >> 0;
			// Step 8.
			var k = relativeStart < 0 ? Math.max(len + relativeStart, 0) : Math.min(relativeStart, len);
			// Steps 9-10.
			var end = arguments[2];
			var relativeEnd = end === undefined ? len : end >> 0;
			// Step 11.
			var final = relativeEnd < 0 ? Math.max(len + relativeEnd, 0) : Math.min(relativeEnd, len);
			// Step 12.
			while (k < final) {
				O[k] = value;
				k++;
			}
			// Step 13.
			return O;
		},
	});
}

class RadialLgbtChart {
	constructor(svgid) {
		this.id = svgid;
		this.svg = d3.select(`#${svgid}`);
		this.chart = this.svg.append('g').attr('id', `chart-${svgid}`);
		this.gauges = this.svg.append('g').attr('id', 'gauges');
		this.defs = this.svg.append('defs');

		this.updateScales();
	}

	/*
    args : {
      enableInteraction, bool : enables features for "mouse over" behavior
      enableLegend, bool : displays legend + interaction between it and the chart
      mirrorsvg, string : second svg identifier when two radial charts need to be synchronized together
    }

    **/
	initData(input, args, horizontal = false) {
		this.data = input;
		this.args = args;

		//let CHARTORDER = ['gouvernance', 'sensibilisation', 'recrutement', 'qualite-de-vie', 'evolution-de-carriere',]

		// DATASET PREPARATION
		let data = input[0] ? input[0] : input;
		data.measures = data.measures.map((d) => {
			return { key: d.key, label: d.label, value: d.value, type: 'main', color: d.color };
		}); //.sort((a, b) => CHARTORDER.indexOf(b.key) - CHARTORDER.indexOf(a.key))

		// LAYOUT PREPARATION
		this.chart.selectAll('*').remove();

		let chartWidth, legendHeight;
		this.chartHeight = (this.height * 2) / 3;
		legendHeight = this.height / 3;
		chartWidth = this.chartHeight;

		const REFDIST = Math.round(Math.min(chartWidth, this.chartHeight) / 2.1);
		const CIRCLESNB = Math.round(Math.min(chartWidth / 10, 50));
		const MAX_SCORE = 100;
		let circleDist = REFDIST * 0.97;
		let dataDist = REFDIST * 0.9;

		let measures = uniq(data.measures.map((measure) => measure.key));

		// CHARTS GENERATION
		this.chart
			.append('g')
			.attr('id', 'imgbg')
			.attr('transform', `translate(${this.width / 2 - REFDIST},${this.chartHeight / 2 - REFDIST})`)
			.append('image')
			.attr('xlink:href', '/static/img/shadow_bckgrd.png')
			.attr('x', 0)
			.attr('y', 0)
			.attr('height', REFDIST * 2)
			.attr('width', REFDIST * 2);

		let gcirclesbg = this.chart
			.append('g')
			.attr('id', 'circlesbg')
			.attr('transform', `translate(${this.width / 2},${this.chartHeight / 2})`);
		let gtopleft = this.chart.append('g').attr('transform', `translate(${this.width / 2 - REFDIST},${this.chartHeight / 2 - REFDIST})`);
		let gaxisbg = this.chart
			.append('g')
			.attr('id', 'axisbg')
			.attr('transform', `translate(${this.width / 2},${this.chartHeight / 2})`);

		// COMPUTE TOOLS
		this.x = function (d) {
			return (dataDist / MAX_SCORE) * d.value * Math.cos(((2 * Math.PI) / measures.length) * measures.indexOf(d.key) - Math.PI / 2);
		};
		this.y = (d) => (dataDist / MAX_SCORE) * d.value * Math.sin(((2 * Math.PI) / measures.length) * measures.indexOf(d.key) - Math.PI / 2);

		// RADAR BACKGROUND DRAW
		gaxisbg
			.append('g')
			.attr('id', 'axes')
			.selectAll('line')
			.data(measures)
			.enter()
			.append('line')
			.attr('class', 'axes')
			.attr('x1', 0)
			.attr('y1', 0)
			.attr('x2', (d, i) => dataDist * Math.cos(((2 * Math.PI) / measures.length) * i - Math.PI / 2))
			.attr('y2', (d, i) => dataDist * Math.sin(((2 * Math.PI) / measures.length) * i - Math.PI / 2));

		gcirclesbg
			.append('g')
			.attr('id', 'circles')
			.selectAll('circle')
			.data(Array(3))
			.enter()
			.append('circle')
			.attr('class', 'axes')
			.attr('cx', 0)
			.attr('cy', 0)
			.attr('r', (d, i) => (dataDist / 3) * (i + 1));

		// RADAR DEFINITION
		this.defs.selectAll('*').remove();
		this.defs
			.append('clipPath')
			.attr('transform', `translate(${REFDIST},${REFDIST})`)
			.attr('id', `${this.id}-mask`)
			.selectAll('path')
			.data([data.measures])
			.enter()
			.append('path')
			.attr(
				'd',
				d3
					.line()
					.x((d) => this.x(d))
					.y((d) => this.y(d)),
			);

		// DECORATION : CIRCLES DEFINITION
		this.defs
			.append('clipPath')
			.attr('transform', `translate(${REFDIST},${REFDIST})`)
			.attr('id', `${this.id}-circlesmask`)
			.selectAll('circle')
			.data(Array(CIRCLESNB))
			.enter()
			.append('circle')
			.attr('cx', (d, i) => 0.98 * circleDist * Math.cos(((2 * Math.PI) / CIRCLESNB) * i - Math.PI / 2))
			.attr('cy', (d, i) => 0.98 * circleDist * Math.sin(((2 * Math.PI) / CIRCLESNB) * i - Math.PI / 2))
			.attr('r', chartWidth / 200);

		// MASKS APPLICATION
		gtopleft
			.append('g')
			.append('image')
			.attr('clip-path', `url(#${this.id}-mask)`)
			.attr('xlink:href', '/static/img/gradient_lgbt2.png')
			.attr('height', REFDIST * 2)
			.attr('width', REFDIST * 2)
			.attr('preserveAspectRatio', 'none');

		gtopleft
			.append('g')
			.append('image')
			.attr('clip-path', `url(#${this.id}-circlesmask)`)
			.attr('xlink:href', '/static/img/gradient_lgbt2.png')
			.attr('height', REFDIST * 2)
			.attr('width', REFDIST * 2)
			.attr('preserveAspectRatio', 'none');

		this.addLegend(data, legendHeight, circleDist * 2, this.width / 2);

		this.scoresGroup = this.chart
			.append('g')
			.attr('id', 'scores')
			.attr('transform', `translate(${this.width / 2},${this.chartHeight / 2})`);
		// CIRCLES THAT STAND FOR DATA
		this.scoresGroup
			.selectAll('circle')
			.data(concat(data.measures, []))
			.enter()
			.append('circle')
			.attr('class', (d) => (d.type === 'main' ? 'data-main' : 'data-compared'))
			.attr('cx', (d) => this.x(d))
			.attr('cy', (d) => this.y(d))
			.attr('r', 5);

		// LABELS TO DISPLAY WHEN MOUSE OVER
		let labelsGroup = this.chart
			.append('g')
			.attr('id', 'labels')
			.attr('transform', `translate(${this.width / 2},${this.chartHeight / 2})`);
		labelsGroup
			.selectAll('text')
			.data(data.measures)
			.enter()
			.append('text')
			.attr('class', 'radar-label hide')
			.attr(
				'transform',
				(d) =>
					`rotate(${(360 / measures.length) * measures.indexOf(d.key) + 90 * (this.x({ key: d.key, value: MAX_SCORE }) >= 0 ? -1 : 1)}, ${this.x({ key: d.key, value: MAX_SCORE })}, ${this.y({ key: d.key, value: MAX_SCORE })})`,
			)
			.attr('x', (d) => this.x({ key: d.key, value: MAX_SCORE }))
			.attr('y', (d) => this.y({ key: d.key, value: MAX_SCORE }))
			.attr('dx', (d) => (this.x({ key: d.key, value: MAX_SCORE }) >= 0 ? -5 : 5))
			.attr('dy', -5)
			.style('text-anchor', (d) => (this.x({ key: d.key, value: MAX_SCORE }) >= 0 ? 'end' : 'start'))
			.text((d) => d.label);

		// "on near" mouse behavior management
		let onnearGroup = this.chart
			.append('g')
			.attr('id', 'onnear')
			.attr('transform', `translate(${this.width / 2},${this.chartHeight / 2})`);
		let onnearData = [];
		measures.forEach(function (measure, i) {
			onnearData.push([
				[
					[0, 0],
					[
						circleDist * Math.cos(((2 * Math.PI) / measures.length) * i - Math.PI / 2 - Math.PI / measures.length),
						circleDist * Math.sin(((2 * Math.PI) / measures.length) * i - Math.PI / 2 - Math.PI / measures.length),
					],
					[
						circleDist * Math.cos(((2 * Math.PI) / measures.length) * i - Math.PI / 2),
						circleDist * Math.sin(((2 * Math.PI) / measures.length) * i - Math.PI / 2),
					],
					[
						circleDist * Math.cos(((2 * Math.PI) / measures.length) * i - Math.PI / 2 + Math.PI / measures.length),
						circleDist * Math.sin(((2 * Math.PI) / measures.length) * i - Math.PI / 2 + Math.PI / measures.length),
					],
					[0, 0],
				],
				{ data: { key: measure } },
			]);
		});

		onnearGroup
			.selectAll('path')
			.data(onnearData)
			.enter()
			.append('path')
			.attr('class', 'voronoi')
			.attr('d', function (d) {
				return d ? 'M' + d[0].join('L') + 'Z' : null;
			})
			.on('mouseover', (d) => {
				this.scoresGroup.selectAll('circle').classed('hide', false);
				this.scoresGroup
					.selectAll('circle')
					.filter((e) => e.key === d[1].data.key)
					.classed('hide', false);

				this.scoresGroup.selectAll('line').classed('hide', true);
				this.scoresGroup
					.selectAll('line')
					.filter((e) => e.key === d[1].data.key)
					.classed('hide', false);

				// labelsGroup.selectAll('text').attr('class', 'hide')
				labelsGroup
					.selectAll('text')
					.filter((e) => e.key === d[1].data.key)
					.classed('hide', false);

				this.chart
					.select('#links')
					.selectAll('line')
					.filter((e) => e.key !== d[1].data.key)
					.classed('disabled', true);

				this.gauges
					.select('#background')
					.selectAll('rect')
					.filter((e) => e.key !== d[1].data.key)
					.classed('disabled', true);
				this.gauges
					.select('#labels')
					.selectAll('text')
					.filter((e) => e.key !== d[1].data.key)
					.classed('disabled', true);
				this.gauges
					.select('#gauge-scores')
					.selectAll('line')
					.filter((e) => e.key !== d[1].data.key)
					.classed('disabled', true);
				this.gauges
					.select('#gauge-scores-mirror')
					.selectAll('line')
					.filter((e) => e.key !== d[1].data.key)
					.classed('disabled', true);
				this.gauges
					.select('#gauge-hints')
					.selectAll('text')
					.filter((e) => e !== d[1].data.key)
					.classed('disabled', true);
				this.gauges
					.select('#gauge-marks')
					.selectAll('line')
					.filter((e) => e !== d[1].data.key)
					.classed('disabled', true);
			})
			.on('mouseout', () => {
				this.scoresGroup.selectAll('circle').classed('hide', true);
				this.scoresGroup.selectAll('line').classed('hide', true);
				labelsGroup.selectAll('text').classed('hide', true);

				this.chart.select('#links').selectAll('line').classed('disabled', false);
				this.gauges.select('#background').selectAll('rect').classed('disabled', false);
				this.gauges.select('#labels').selectAll('text').classed('disabled', false);
				this.gauges.select('#gauge-scores').selectAll('line').classed('disabled', false);
				this.gauges.select('#gauge-scores-mirror').selectAll('line').classed('disabled', false);
				this.gauges.select('#gauge-hints').selectAll('text').classed('disabled', false);
				this.gauges.select('#gauge-marks').selectAll('line').classed('disabled', false);
			});
	}

	addLegend(data, LEGENDHEIGHT, LEGENDWIDTH, REFDIST) {
		let _this = this;
		const LEGENDORDER = data.measures.map((d) => d.key); //['gouvernance', 'sensibilisation', 'recrutement', 'qualite-de-vie', 'evolution-de-carriere', 'suggestions'].reverse()
		const PADDING = 5;
		const GAUGEPADDING = PADDING * 3;
		const GAUGEHEIGHT = 6;
		let measures = data.measures.sort((a, b) => -LEGENDORDER.indexOf(b.key) + LEGENDORDER.indexOf(a.key));

		this.gauges
			.attr('transform', `translate(${this.width / 2}, ${this.chartHeight})`)
			.selectAll('*')
			.remove();

		let disableLinks = function (g) {
			g.on('mouseover', (d) => {
				_this.chart
					.select('#links')
					.selectAll('line')
					.filter((e) => e.key !== d.key)
					.classed('disabled', true);
				_this.gauges
					.select('#background')
					.selectAll('rect')
					.filter((e) => e.key !== d.key)
					.classed('disabled', true);
				_this.gauges
					.select('#labels')
					.selectAll('text')
					.filter((e) => e.key !== d.key)
					.classed('disabled', true);
				_this.gauges
					.select('#gauge-scores')
					.selectAll('line')
					.filter((e) => e.key !== d.key)
					.classed('disabled', true);
				_this.gauges
					.select('#gauge-marks')
					.selectAll('line')
					.filter((e) => e !== d.key)
					.classed('disabled', true);
				_this.gauges
					.select('#gauge-hints')
					.selectAll('text')
					.filter((e) => e !== d.key)
					.classed('disabled', true);
			}).on('mouseout', () => {
				_this.chart.select('#links').selectAll('line').classed('disabled', false);
				_this.gauges.select('#background').selectAll('rect').classed('disabled', false);
				_this.gauges.select('#labels').selectAll('text').classed('disabled', false);
				_this.gauges.select('#gauge-scores').selectAll('line').classed('disabled', false);
				_this.gauges.select('#gauge-marks').selectAll('line').classed('disabled', false);
				_this.gauges.select('#gauge-hints').selectAll('text').classed('disabled', false);
			});
		};

		let background = this.gauges.append('g').attr('id', 'background');
		let labels = this.gauges.append('g').attr('id', 'labels');
		labels
			.selectAll('text')
			.data(measures)
			.enter()
			.append('text')
			.attr('id', (d) => d.key)
			.attr('class', (d) => `category label-${d.key}`)
			.attr('x', 0)
			.attr('y', 0)
			.style('font-family', `Cousine`)
			.attr('fill', 'white')
			.style('font-size', `${LEGENDHEIGHT / measures.length / 3}px`)
			.text((d) => d.label)
			.call(disableLinks);

		let LABELHEIGHT =
			labels
				.select(`[id=` + LEGENDORDER[0] + `]`)
				.node()
				.getBBox().height +
			PADDING * 2;
		labels.selectAll('text').attr('y', (d, i) => i * LABELHEIGHT * 1.3);

		background
			.selectAll('rect')
			.data(measures)
			.enter()
			.append('rect')
			.attr('class', (d) => `label-fill-${d.key}`)
			.attr('fill', (d) => d.color)
			.attr('x', (d) => labels.select(`[id="${d.key}"]`).node().getBBox().x - PADDING)
			.attr('y', (d) => labels.select(`[id="${d.key}"]`).node().getBBox().y - PADDING)
			.attr('width', (d) => labels.select(`[id="${d.key}"]`).node().getBBox().width + PADDING * 2)
			.attr('height', (d) => LABELHEIGHT);

		// compute the max size of the labels in order to translate the whole <g> to the bottom
		let maxRectSize = [];
		background.selectAll('rect').each(function (d) {
			maxRectSize.push(parseFloat(d3.select(this).attr('width')));
		});
		maxRectSize = max(maxRectSize);

		const GAUGEWIDTH = LEGENDWIDTH - maxRectSize - GAUGEPADDING;

		let marks = [];
		LEGENDORDER.forEach((d) => marks.push(Array(11).fill(d)));
		marks = flatten(marks);

		this.gauges
			.append('g')
			.attr('id', 'gauge-marks')
			.attr('transform', `translate(${GAUGEPADDING},0)`)
			.selectAll('line')
			.data(marks)
			.enter()
			.append('line')
			.attr('class', 'gauge-mark')
			.attr('x1', (d, i) => ((i % 11) * GAUGEWIDTH) / 10)
			.attr('y1', (d, i) => Math.floor(i / 11) * LABELHEIGHT * 1.3 - GAUGEHEIGHT / 2)
			.attr('x2', (d, i) => ((i % 11) * GAUGEWIDTH) / 10)
			.attr('y2', (d, i) => Math.floor(i / 11) * LABELHEIGHT * 1.3 - GAUGEHEIGHT);

		let hints = [];
		LEGENDORDER.forEach((d) => hints.push(Array(2).fill(d)));
		hints = flatten(hints);
		this.gauges
			.append('g')
			.attr('id', 'gauge-hints')
			.attr('transform', `translate(${GAUGEPADDING},0)`)
			.selectAll('text')
			.data(hints)
			.enter()
			.append('text')
			.attr('class', 'gauge-hint')
			.attr('x', (d, i) => (i % 2) * GAUGEWIDTH)
			.attr('y', (d, i) => Math.floor(i / 2) * LABELHEIGHT * 1.3 - GAUGEHEIGHT * 1.5)
			.text((d, i) => (i % 2 === 0 ? '-' : '+'));

		this.gauges
			.append('g')
			.attr('id', 'gauge-scores')
			.attr('transform', `translate(${GAUGEPADDING},0)`)
			.selectAll('line')
			.data(measures)
			.enter()
			.append('line')
			.attr('class', (d) => `gauge gauge-${d.key}`)
			.attr('stroke', (d) => d.color)
			.attr('x1', 0)
			.attr('y1', (d, i) => i * LABELHEIGHT * 1.3)
			.attr('x2', (d) => (d.value * GAUGEWIDTH) / 100)
			.attr('y2', (d, i) => i * LABELHEIGHT * 1.3)
			.attr('stroke-linecap', 'round')
			.call(disableLinks);

		this.chart
			.append('g')
			.attr('id', 'links')
			.selectAll('line')
			.data(measures)
			.enter()
			.append('line')
			.attr('class', (d) => `link-category link-${d.key}`)
			.attr('stroke', (d) => d.color)
			.attr('x1', (d) => this.width / 2 + this.x(d))
			.attr('y1', (d) => this.chartHeight / 2 + this.y(d))
			.attr(
				'x2',
				(d) =>
					REFDIST -
					(-maxRectSize + GAUGEWIDTH + GAUGEPADDING) / 2 +
					parseFloat(background.select(`.label-fill-${d.key}`).attr('x')) +
					(d.key === 'lgbt' || d.key === 'generational_diversity' ? parseFloat(background.select(`.label-fill-${d.key}`).attr('width')) : 0),
			)
			.attr('y2', (d) => this.chartHeight + parseFloat(background.select(`.label-fill-${d.key}`).attr('y')) + LABELHEIGHT);
		// Center the whole legend
		this.gauges.attr('transform', `translate(${REFDIST - (-maxRectSize + GAUGEWIDTH + GAUGEPADDING) / 2}, ${this.chartHeight + LABELHEIGHT})`);
	}

	rerender() {
		this.updateScales();
		this.initData(this.data, this.args);
	}

	updateScales() {
		this.width = this.svg.attr('width');
		this.height = this.svg.attr('height');
	}
}

export default RadialLgbtChart;

/* global d3 */
import concat from 'lodash-es/concat';
import uniq from 'lodash-es/uniq';

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

class RadialChart {
	constructor(svgid) {
		this.id = svgid;
		this.svg = d3.select(`#${svgid}`);
		this.chart = this.svg.append('g').attr('id', `chart-${svgid}`);
		this.defs = this.svg.append('defs');
		this.blocked_url = '/static/img/picto_lock.png';

		this.updateScales();
	}

	/*
      args : {
        enableInteraction, bool : enables features for "mouse over" behavior
        enableLegend, bool : displays legend + interaction between it and the chart
        mirrorsvg, string : second svg identifier when two radial charts need to be synchronized together
      }

      **/
	initData(input, args) {
		this.data = input;
		this.args = args;

		let CHARTORDER = ['disability', 'cultural_diversity', 'generational_diversity', 'lgbt', 'gender'];
		let background_url = '/static/img/gradient.png';

        // DATASET PREPARATION
        let data = input[0] ? input[0] : input;
        if (data.footprint_type !== undefined && data.footprint_type !== null && data.footprint_type !== 'standard') {
            background_url = '/static/img/' + data.footprint_type + '.png';
        }
        data.measures.forEach((cat) => {
            if (cat.fake === 1) {
                if (cat.label.split(' ').length < 2) {
                    cat.label += ' '.repeat(8); // 8 unbreakable spaces to make space for the blocked icon
                }
            } else if (data.type === 'evaluation_collaborateurs_360') {
                background_url = '/static/img/backMixityHuman.png';
            }
        })
        data.measures = data.measures
			.map((d) => {
				return { key: d.key, label: d.label, value: d.value, type: 'main', fake: d.fake, color: d.color }
			})
			.sort((a, b) => CHARTORDER.indexOf(b.key) - CHARTORDER.indexOf(a.key));

		let comparedData = input.length === 2 ? input[1] : undefined;
		if (comparedData) {
			comparedData.measures = comparedData.measures
				.map((d) => {
					return { key: d.key, label: d.label, value: d.value, type: 'compared', fake: d.fake, color: d.color };
				})
				.sort((a, b) => CHARTORDER.indexOf(b.key) - CHARTORDER.indexOf(a.key));
		}

		// LAYOUT PREPARATION
		this.chart.selectAll('*').remove();

		let chartWidth;
		chartWidth = this.width;
		if (args && args.enableLegend) {
			this.chartHeight = chartWidth;
		} else {
			this.chartHeight = this.height;
		}

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
		let gcomparedData;

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

		// Pattern de hachures
		this.defs
			.append('pattern')
			.attr('id', 'diagonalHatch')
			.attr('patternUnits', 'userSpaceOnUse')
			.attr('width', 4)
			.attr('height', 4)
			.append('path')
			.attr('d', 'M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2')
			.attr('style', 'stroke:#5f6263; stroke-width:1');

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
			.attr('xlink:href', background_url)
			.attr('height', REFDIST * 2)
			.attr('width', REFDIST * 2)
			.attr('preserveAspectRatio', 'none');

		gtopleft
			.append('g')
			.append('image')
			.attr('clip-path', `url(#${this.id}-circlesmask)`)
			.attr('xlink:href', background_url)
			.attr('height', REFDIST * 2)
			.attr('width', REFDIST * 2)
			.attr('preserveAspectRatio', 'none');

		if (comparedData !== undefined) {
			// ADD COMPARED DATA IF ANY
			gcomparedData = this.chart.append('g').attr('transform', `translate(${this.width / 2},${this.chartHeight / 2})`);

			gcomparedData
				.selectAll('path')
				.data([comparedData.measures])
				.enter()
				.append('path')
				.attr(
					'd',
					d3
						.line()
						.x((d) => this.x(d))
						.y((d) => this.y(d))
						.curve(d3.curveLinearClosed),
				)
				.attr('class', 'compared-path');

			gcomparedData.append('text').attr('x', 0).attr('y', 0).attr('class', 'society-name').text(comparedData.society);
		}

		if (args && args.enableInteraction) {
			this.scoresGroup = this.chart
				.append('g')
				.attr('id', 'scores')
				.attr('transform', `translate(${this.width / 2},${this.chartHeight / 2})`);

			// CIRCLES THAT STAND FOR DATA
			this.scoresGroup
				.selectAll('circle')
				.data(concat(data.measures, comparedData !== undefined ? comparedData.measures : []))
				.enter()
				.append('circle')
				.attr('class', function (d) {
					let class_name = d.type === 'main' ? 'data-main' : 'data-compared';
					if (d.fake === 1) {
						// class_name += ' fake_circle'
					}
					class_name += ' circle_data';
					return class_name;
				})
				.attr('cx', (d) => this.x(d))
				.attr('cy', (d) => this.y(d))
				.attr('r', 5)
				.attr('style', function (d) {
					if (d.fake === 1) {
						return 'fill:#b3bbbd';
					}
				});

			let SCORE_GROUPS_BLOCKED_POSITION = [
				{
					x: '-2.5%',
					y: '-21.5%',
				},
				{
					x: '-21%',
					y: '-8%',
				},
				{
					x: '-13%',
					y: '13%',
				},
				{
					x: '9%',
					y: '13%',
				},
				{
					x: '15%',
					y: '-8.5%',
				},
			];
			let scoreIndex = 0;
			this.scoresGroup
				.selectAll('.circle_data')
				.nodes()
				.forEach((circleData) => {
					if (circleData.classList.contains('fake_circle')) {
						this.scoresGroup
							.append('svg:image')
							.attr('width', 30)
							.attr('height', 30)
							.attr('xlink:href', this.blocked_url)
							.attr('x', function () {
								if (SCORE_GROUPS_BLOCKED_POSITION[scoreIndex] !== undefined) {
									return SCORE_GROUPS_BLOCKED_POSITION[scoreIndex].x;
								}
							})
							.attr('y', function () {
								if (SCORE_GROUPS_BLOCKED_POSITION[scoreIndex] !== undefined) {
									return SCORE_GROUPS_BLOCKED_POSITION[scoreIndex].y;
								}
							});
					}
					scoreIndex++;
				});

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
				})
				.on('mouseout', () => {
					this.scoresGroup.selectAll('circle').classed('hide', true);
					this.scoresGroup.selectAll('line').classed('hide', true);

					this.chart.select('#links').selectAll('line').classed('disabled', false);

					if (comparedData !== undefined) {
						gcomparedData.select('path').transition().style('fill-opacity', 0);
						gcomparedData.select('text').transition().style('opacity', 0);

						if (args && args.mirrorsvg && args.mirrorsvg.length > 0) {
							let mirror = d3.select(`#${args.mirrorsvg}`);

							mirror.select(`#scores`).selectAll('circle').classed('hide', true);
							mirror.select(`#scores`).selectAll('line').classed('hide', true);
							mirror.select('#links').selectAll('line').classed('disabled', false);
						}
					}
				});
		}
	}

	updateScales() {
		this.width = this.svg.attr('width');
		this.height = this.svg.attr('height');
	}
}

export default RadialChart;

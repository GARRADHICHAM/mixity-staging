module.exports = (ctx) => ({
	map: ctx.options.map,
	plugins: [
		require('postcss-import')(),
		require('postcss-css-variables')(),
		require('postcss-custom-properties')(),
		require('postcss-hexrgba'),
		require('autoprefixer')({ grid: 'autoplace' }),
		require('postcss-preset-env')({
			stage: 2,
		}),
		require('postcss-media-minmax')(),
		require('postcss-nested'),
		require('postcss-url')([
			// Font Awesome
			{
				filter: '**/webfonts/**.*',
				url: 'copy',
				useHash: false,
				assetsPath: 'node_modules',
			},
			// Other assets
			{
				url: 'inline',
			},
		]),
		require('cssnano')(ctx.env === 'production' ? {} : false),
	],
});

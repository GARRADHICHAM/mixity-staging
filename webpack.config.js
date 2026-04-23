const path = require('path');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const BrowserSyncPlugin = require('browser-sync-webpack-plugin');
const { version } = require('./package.json');
const CopyWebpackPlugin = require('copy-webpack-plugin');
//const PrettierPlugin = require("prettier-webpack-plugin");
// add "prettier": "^1.0.0","prettier-webpack-plugin": "^1.2.0", in package.json
const glob = require('glob');
module.exports = ({ mode = 'development' } = {}) => {
	const isProductionBuild = mode === 'production';

	const defaultPlugins = [
		new CopyWebpackPlugin({
			patterns: [{ from: `./theme/src/webfonts`, to: 'static/dist/webfonts' }],
		}),
	];
	const productionPlugins = [
		new CleanWebpackPlugin({
			cleanAfterEveryBuildPatterns: ['build'],
		}),
	];
	const filesToWatch = [
		`./theme/src/scss/**/*.scss`,
		`./theme/src/js/**/*.js`,
		`./collaborator_evaluation/src/js/**/*.js`,
		`./collaborator_evaluation/src/scss/**/*.scss`,
	];
	const devPlugins = [
		new BrowserSyncPlugin({
			proxy: 'web:8000',
			port: 3009,
			files: filesToWatch,
			reloadDelay: 0,
			notify: false,
			open: false,
			https: true,
		}),
		// new PrettierPlugin()
	];
	return {
		entry: {
			index: [path.resolve(__dirname, `./theme/src/js/index.js`), ...glob.sync(path.resolve(__dirname, `./theme/src/js/indicators/**.js`))],
			collaboratorevaluation: path.resolve(__dirname, `./collaborator_evaluation/src/js/index.js`),

			styles: path.resolve(__dirname, `./theme/src/scss/style.scss`),
			collaboratorsevaluationstyles: path.resolve(__dirname, `./collaborator_evaluation/src/scss/collaboratorsevaluation.scss`),

			dashboardhomecomponents: path.resolve(__dirname, `./mixity/dashboard/js/index.js`),

			leadcomponents: path.resolve(__dirname, `./lead/js/index.js`),
			overviewleadcomponents: path.resolve(__dirname, `./lead/js/indexOverview.js`),

			dashboardstyle: path.resolve(__dirname, `./theme/src/scss/dashboard_style.scss`),

			dashboardlandingdiagcomponents: path.resolve(__dirname, `./landing/dashboard/js/dashboardLandingDiag.js`),
			dashboardlandinghumancomponents: path.resolve(__dirname, `./landing/dashboard/js/dashboardLandingHuman.js`),
			dashboardlandingmeasurecomponents: path.resolve(__dirname, `./landing/dashboard/js/dashboardLandingMeasure.js`),
			dashboardlandingpilotcomponents: path.resolve(__dirname, `./landing/dashboard/js/dashboardLandingPilot.js`),
			dashboardlandingsolvercomponents: path.resolve(__dirname, `./landing/dashboard/js/dashboardLandingSolver.js`),

			dashboardlogincomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardLogin.js`),
			dashboardregisterstartcomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardRegisterStart.js`),
			dashboardregisterstartconfirmedcomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardRegisterStartConfirmed.js`),
			dashboardregisterconfirmedcomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardRegisterConfirmed.js`),
			dashboardregistercomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardRegister.js`),
			dashboardmailvalidationcomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardMailValidation.js`),
			dashboardcreatestructurecomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardCreateStructure.js`),
			dashboardforgottenpasswordmailcomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardSendLinkForgottenMail.js`),
			dashboardforgottenpasswordchangecomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardForgottenPasswordChange.js`),

			invitationconfirmedcomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardInvitationConfirmed.js`),
			invitationcreatepasswordcomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardInvitationCreatePassword.js`),

			dashboardprofileupdatecomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardUpdateProfile.js`),
			dashboardpasswordchangecomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardPasswordChange.js`),
			dashboardstructureupdatecomponents: path.resolve(__dirname, `./accounts/dashboard/js/dashboardStructureUpdate.js`),

			nameanalyzercomponents: path.resolve(__dirname, `./mixity/dashboard/js/nameAnalyzer.js`),
			adpstatuscomponents: path.resolve(__dirname, `./sirh/js/index.js`),
			adprequestcomponents: path.resolve(__dirname, `./sirh/js/adpRequestPage.js`),
			adpindicatorscomponents: path.resolve(__dirname, `./sirh/js/adpIndicatorsPage.js`),
			nameanalyzeruploadcomponents: path.resolve(__dirname, `./mixity/dashboard/js/nameAnalyzerUpload.js`),
			actsolutionscomponents: path.resolve(__dirname, `./act/js/actSolutions.js`),
			questiontypegeneratorcomponents: path.resolve(__dirname, `./mixity/admin_r/js/questionTypeGenerator.js`),
			actfavoritescomponents: path.resolve(__dirname, `./act/js/actFavorites.js`),
			actsolversolutionscomponents: path.resolve(__dirname, `./act/js/actSolverSolutions.js`),
			actbestpracticesmanagementcomponents: path.resolve(__dirname, `./act/js/actBestPracticesManagement.js`),
			actbestpracticescomponents: path.resolve(__dirname, `./act/js/actBestPractices.js`),
			actfavoritebestpracticescomponents: path.resolve(__dirname, `./act/js/actFavoriteBestPractices.js`),
			crispcomponents: path.resolve(__dirname, `./mixity/src/js/crisp-config.js`),
			actelearningslistcomponents: path.resolve(__dirname, `./act/js/actElearningsList.js`),
			actelearningdetailscomponents: path.resolve(__dirname, `./act/js/actElearningDetails.js`),
			actlandingelearningscomponents: path.resolve(__dirname, `./act/js/actLandingElearnings.js`),

			assessdashboardhomecomponents: path.resolve(__dirname, `./scoring/dashboard/js/dashboardAssessPage.js`),
			evaluationcriteriascomponents: path.resolve(__dirname, `./scoring/dashboard/js/dashboardEvaluationCriteriasPage.js`),
			evaluationsurveycomponents: path.resolve(__dirname, `./scoring/dashboard/js/dashboardEvaluationSurveyPage.js`),
			indicatorcreatingdashboardhomecomponents: path.resolve(__dirname, `./scoring/dashboard/js/dashboardIndicatorCreatingPage.js`),
			assessdashboardhomePDF: path.resolve(__dirname, `./scoring/pdf_generator/js/dashboardAssessPage_Pdf.js`),
			dashboardcollaboratorscorecardcomponents: path.resolve(__dirname, `./scoring/dashboard/js/dashboardCollaboratorScoreCardPage.js`),
		},
		output: {
			filename: `static/dist/js/[name]-${version}.js`,
			chunkFilename: `static/dist/js/[name]-${version}.js`,
			path: path.resolve(__dirname, `./mixity`),
			publicPath: '/',
			library: 'Mixity',
		},
		module: {
			rules: [
				{
					test: /\.js$/,
					use: {
						loader: 'babel-loader',
						options: {
							presets: ['@babel/preset-env', '@babel/react'],
						},
					},
				},
				{
					test: /\.html$/,
					use: {
						loader: 'html-loader',
					},
				},
				{
					test: /\.(png|svg|jpg|gif)$/,
					use: {
						loader: 'file-loader',
					},
				},
				{
					test: /\.(eot|svg|ttf|woff|woff2|otf)$/,
					loader: 'file-loader',
				},
				{
					test: /\.css$/i,
					use: ['style-loader', 'css-loader'],
				},
				{
					test: /\.s[ac]ss$/i,
					use: [
						{
							loader: 'file-loader',
							options: {
								name: `static/dist/css/[name]-${version}.css`,
							},
						},
						{
							loader: 'extract-loader',
						},
						{
							loader: 'css-loader',
							options: {
								url: false,
							},
						},
						{
							loader: 'postcss-loader',
						},
						{
							loader: 'sass-loader',
						},
					],
				},
			],
		},
		plugins: [...defaultPlugins, ...(isProductionBuild ? productionPlugins : devPlugins)],
		devtool: isProductionBuild ? 'source-map' : false,
		devServer: {
			open: true,
			host: '0.0.0.0',
			proxy: {
				'/': {
					target: 'http://web:8000',
				},
			},
			watchFiles: {
				options: {
					awaitWriteFinish: {
						stabilityThreshold: 2000,
					},
				},
				paths: filesToWatch,
			},
		},
	};
};

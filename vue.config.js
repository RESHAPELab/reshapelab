const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
  publicPath: process.env.NODE_ENV === 'production' ? '/research_lab_website/' : '/',
  outputDir: 'dist',
  assetsDir: 'assets',
  indexPath: 'index.html',
  filenameHashing: true,
  productionSourceMap: false,

  chainWebpack: config => {
    config.module
      .rule('woff')
      .test(/\.woff$/)
      .use('file-loader')
      .loader('file-loader')
      .tap(options => {
        return {
          name: '[path][name].[ext]'
        };
      });
  }
};

const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack');

module.exports = [
  {
    mode: 'production',
    entry: './src/webui/web_react.tsx',
    module: {
      rules: [
        {
          test: /\.ts(x?)$/,
          include: /src/,
          use: [{ loader: 'ts-loader' }]
        },
        {
          test: /\.css$/i,
          use: ["style-loader", "css-loader"],
        },
        {
          test: /\.(svg|png|jpg)$/,
          loader: 'file-loader'
        },
      ]
    },
    output: {
      path: __dirname + '/public/web',
      filename: 'web_react.js'
    },
    resolve: {
      extensions: ['.ts', '.tsx', '.js']
    },
  }
];
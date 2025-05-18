const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack');

module.exports = [
  {
    mode: 'development',
    entry: './src/webui/web_react.tsx',
    devtool: "source-map",
    devServer: {
      port: 7481,
    },
    module: {
      rules: [
        {
          test: /\.ts(x?)$/,
          include: /src/,
          use: [{ loader: 'ts-loader', options: { 'transpileOnly': true, } }]
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
      path: __dirname + '/../src/static',
      filename: 'web_react.js'
    },
    resolve: {
      extensions: ['.ts', '.tsx', '.js']
    },
  }
];
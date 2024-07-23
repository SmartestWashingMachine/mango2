const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack');

module.exports = [
  {
    mode: 'production',
    entry: './src/electron.ts',
    target: 'electron-main',
    module: {
      rules: [
        {
          test: /\.ts$/,
          include: /src/,
          use: [{ loader: 'ts-loader', options: { 'transpileOnly': true, } }]
        },
        {
          test: /\.node$/,
          loader: "node-loader",
        },
        {
          test: /\.(svg|png|jpg)$/,
          loader: 'file-loader'
        },
      ]
    },
    output: {
      path: __dirname + '/public',
      filename: 'electron.js'
    },
    plugins: [

    ],
    resolve: {
      extensions: ['.ts', '.tsx', '.js']
    },
    externals: {
      'sharp': 'commonjs sharp',
      bufferutil: "bufferutil",
      "utf-8-validate": "utf-8-validate",
    }
  },

  {
    mode: 'production',
    entry: './src/preload.js',
    target: 'electron-preload',
    output: {
      path: __dirname + '/public',
      filename: 'preload.js',
    },
  },

  {
    mode: 'production',
    entry: './src/react.tsx',
    target: 'electron-renderer',
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
      path: __dirname + '/public',
      filename: 'react.js'
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './src/index.html'
      }),
      new webpack.DefinePlugin({
        '__REACT_DEVTOOLS_GLOBAL_HOOK__': '({ isDisabled: true })'
      }),
    ],
    resolve: {
      extensions: ['.ts', '.tsx', '.js']
    },
  }
];
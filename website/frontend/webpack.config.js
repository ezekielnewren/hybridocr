const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: './src/index.ts',     // Entry point for your TypeScript code
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'dist')
  },
  resolve: {
    extensions: ['.ts', '.js']
  },
  module: {
    rules: [
      {
        test: /\.ts$/,          // Use ts-loader to compile TypeScript files
        use: 'ts-loader',
        exclude: /node_modules/
      }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './src/index.html'  // Template HTML file
    })
  ],
  devServer: {
    static: './dist',           // Serve static files from the 'dist' directory
    compress: true,
    port: 9000
  }
};

'use strict';

var AWS = require('aws-sdk');

var cognito = new AWS.CognitoIdentityServiceProvider();

exports.handler = function (event, context, callback) {
    cognito.listUsers({
        UserPoolId: 'us-east-2_Ho68tdkU2',
        AttributesToGet: [],
        Filter: '',
        Limit: 60
    }, function (err, data) {
        if (err === null) {
            var logins = [];
            data.Users.forEach(function (user) {
                if (event.cognitoUsername !== user.Username) {
                    logins.push(user.Username);
                }
            });
            callback(null, logins);
        } else {
            callback(err);
        }
    });
};
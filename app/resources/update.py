from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request

from models.user import UserModel
from schemas.user import UserSchema
from user_functions.record_user_log import record_user_log

api = Namespace('update', description='Update User')

user_schema = UserSchema()
users_schema = UserSchema(many=True)

user_model = api.model('User', {
    'full_name': fields.String(required=True, description='Full Name'),
    'email': fields.String(required=True, description='Email'),
    'phone': fields.String(required=True, description='Phone'),
})

@api.route('/<int:id>')
@api.param('id', 'The user identifier')
class UpdateUser(Resource):
    @api.doc('Update user')
    @api.expect(user_model)
    @jwt_required
    def put(self,id:int):
        '''Update User'''
        try:
            my_user = UserModel.fetch_by_id(id)
            user = user_schema.dump(my_user)
            if len(user) == 0:
                return {'message':'User does not exist'}, 404

            authorised_user = get_jwt_identity()
            if id != authorised_user['id']:
                return {'message':'You cannot modify this user! Please log in as this user to modify.'}, 403

            data = api.payload
            if not data:
                return {'message':'No input data detected'}, 400

            email = data['email'].lower()

            db_user = UserModel.fetch_by_email(email)
            user_to_check = user_schema.dump(db_user)
            if len(user_to_check) > 0:
                if email == user_to_check['email'] and id != user_to_check['id']:
                    return {'message':'Falied... A user with this email already exists'}, 400

            phone = data['phone']
            db_user = UserModel.fetch_by_phone(phone)
            user_to_check = user_schema.dump(db_user)
            if len(user_to_check) > 0:
                if phone == user_to_check['phone'] and id != user_to_check['id']:
                    return {'message':'Falied... A user with this phone number already exists'}, 400

            full_name = data['full_name'].lower()

            UserModel.update(id=id, email=email, full_name=full_name, phone=phone)

            this_user = UserModel.fetch_by_email(email)
            

            # Record this event in user's logs
            log_method = 'put'
            log_description = 'Updated user details'

            authorization = request.headers.get('Authorization')
            auth_token  = { "Authorization": authorization}
            record_user_log(auth_token, log_method, log_description)

            return user_schema.dump(this_user), 200
        except Exception as e:
            print('========================================')
            print('error description: ', e)
            print('========================================')
            return {'message': 'Could not update user.'}, 500

#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Character, CharacterAttribute
from utils.helpers import exp_for_level, apply_level_up

def debug_levelup():
    with app.app_context():
        # Clean up any existing test data
        User.query.filter_by(username='debug_test').delete()
        db.session.commit()

        # Create a test user
        test_user = User(username='debug_test', password_hash='test', email='debug@example.com')
        db.session.add(test_user)
        db.session.commit()

        # Create a test character
        test_char = Character(
            user_id=test_user.id,
            name='DebugChar',
            linggen='火',
            wuxing=50,
            qiyun=50,
            level=1,
            experience=0,
            realm='凡人期'
        )
        db.session.add(test_char)
        db.session.flush()

        # Create character attributes
        test_attr = CharacterAttribute(
            character_id=test_char.id,
            hp=100,
            attack=10,
            defense=10,
            speed=10,
            crit_rate=0.05,
            dodge_rate=0.05,
            hit_rate=0.95,
            crit_damage=1.5
        )
        db.session.add(test_attr)

        # Add linggen bonus for 火
        test_attr.attack += 8
        test_attr.crit_rate += 0.02

        db.session.commit()

        print(f"Initial character level: {test_char.level}")
        print(f"Initial character experience: {test_char.experience}")

        # Calculate needed experience for level 1
        needed_exp = exp_for_level(test_char.level)
        print(f"Experience needed for level {test_char.level}: {needed_exp}")

        # Set character experience to exactly the amount needed
        test_char.experience = needed_exp
        db.session.commit()

        print(f"Character experience after setting: {test_char.experience}")

        # Get realm coefficient
        from models import Realm
        realm = Realm.query.filter_by(name=test_char.realm).first()
        realm_coeff = realm.coefficient if realm else 0.0
        print(f"Realm coefficient: {realm_coeff}")

        # Simulate levelup process
        print("\n=== Starting levelup process ===")

        # Check if level is multiple of 10
        if test_char.level % 10 == 0:
            print("ERROR: Level is multiple of 10, should not be able to level up!")
            return

        # Deduct experience
        test_char.experience -= needed_exp
        print(f"Experience after deduction: {test_char.experience}")

        # Apply level up
        increments = apply_level_up(test_char, test_attr, realm_coeff)
        print(f"Level after apply_level_up: {test_char.level}")
        print(f"Attribute increments: {increments}")

        db.session.commit()

        print(f"Final character level: {test_char.level}")
        print(f"Final character experience: {test_char.experience}")

if __name__ == '__main__':
    debug_levelup()

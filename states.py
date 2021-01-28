import pygame as pg
from nodes import State


class Dead(State):
    def __init__(self, states):
        State.__init__(self, [], states)

    def enter(self, entity):
        entity.timer = 0
        entity.sprite.play("dead")


class Idle(State):
    def __init__(self, states):
        State.__init__(self, [Jump, Fall, Walk], states)

    @staticmethod
    def check(entity):
        if entity.state.current("Skid"):
            return abs(entity.velocity.x + entity.input_velocity.x) == abs(entity.velocity.x) + abs(entity.input_velocity.x)
        return entity.grounded and entity.velocity.x == 0

    def enter(self, entity):
        entity.sprite.play("idle")


class Walk(State):
    def __init__(self, states):
        State.__init__(self, [Fall, Jump, Skid, Idle], states)

    @staticmethod
    def check(entity):
        return entity.grounded and entity.velocity.x != 0

    def enter(self, entity):
        entity.sprite.play("walk")


class Skid(State):
    def __init__(self, states):
        State.__init__(self, [Fall, Jump, Idle], states)

    @staticmethod
    def check(entity):
        return (
            entity.velocity.x > 0 and entity.input_velocity.x < 0
        ) or (
            entity.velocity.x < 0 and entity.input_velocity.x > 0
        )

    def enter(self, entity):
        entity.sprite.play("skid")

class Jump(State):
    def __init__(self, states):
        State.__init__(self, [Fall, Idle, Walk], states)

    @staticmethod
    def check(entity):
        return entity.velocity.y < 0

    def enter(self, entity):
        entity.sprite.play("jump")


class Fall(State):
    def __init__(self, states):
        State.__init__(self, [Jump, Idle, Walk], states)

    @staticmethod
    def check(entity):
        if entity.state.current("ClimbIdle") or entity.state.current("ClimbMove"):
            return not entity.is_near("ladder")
        return not entity.grounded and entity.velocity.y > 0

    def enter(self, entity):
        entity.sprite.play("fall")


class ClimbIdle(State):
    def __init__(self, states):
        State.__init__(self, [Fall, ClimbMove], states)

    @staticmethod
    def check(entity):
        return entity.velocity == pg.Vector2(0,0)

    def enter(self, entity):
        entity.gravity = False
        entity.sprite.play("climb_idle")

    def exit(self, entity):
        entity.gravity = True


class ClimbMove(State):
    def __init__(self, states):
        State.__init__(self, [Fall, ClimbIdle], states)

    @staticmethod
    def check(entity):
        return entity.velocity != pg.Vector2(0,0)

    def enter(self, entity):
        entity.gravity = False
        entity.sprite.play("climb_move")

    def exit(self, entity):
        entity.gravity = True

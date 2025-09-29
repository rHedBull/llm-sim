


# questions
- how can I properly test it, complex simulation
- ui/ux, ready?
- do we get proper data out of it?

# todo

- [ ] remove all legacy support, so no silent failure, no migration 
- refactor 
- self.game_engine.calculate_new_state  and outcomes = await self.game_engine.process_actions(actions, self.current_state)  seem to not exist, game engine seems not up to date
- state manager in simulation is unised? 
- still no state management persistancy, database, analysis? restarting at a certain state?
- horrible error reporting, much silent failure!
- so many data classes, all needed, simplify comibne, inherit?

each run unique id, storing of them


# problems
what is state handler?

state view?
resolve really only single agent class, no three layer, no legacy ....
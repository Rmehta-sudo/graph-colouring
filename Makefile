CXX := g++
CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -I src
LDFLAGS :=

SRC_DIR := src
BUILD_DIR := build
TARGET := $(BUILD_DIR)/benchmark_runner

SOURCES := \
	$(SRC_DIR)/benchmark_runner.cpp \
	$(SRC_DIR)/io/graph_loader.cpp \
	$(SRC_DIR)/io/graph_writer.cpp \
	$(SRC_DIR)/io/results_logger.cpp \
	$(SRC_DIR)/algorithms/genetic.cpp \
	$(SRC_DIR)/algorithms/welsh_powell.cpp \
	$(SRC_DIR)/algorithms/dsatur.cpp \
	$(SRC_DIR)/algorithms/simulated_annealing.cpp \
	$(SRC_DIR)/algorithms/exact_solver.cpp \
	$(SRC_DIR)/algorithms/tabu.cpp

OBJECTS := $(SOURCES:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)

.PHONY: all clean run-genetic run-welsh run-dsatur run-exact run-sa run-tabu run-all-benchmarking help

GRAPH ?= dimacs/myciel6.col
GRAPH_PATH := data/$(GRAPH)
GRAPH_FILE := $(notdir $(GRAPH))
GRAPH_NAME := $(basename $(GRAPH_FILE))
OUTPUT ?= results/colourings/$(GRAPH_NAME)_genetic.col
RESULTS ?= results/results.csv
SNAPSHOTS ?= 0

all: $(TARGET)

$(TARGET): $(OBJECTS)
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(OBJECTS) -o $@ $(LDFLAGS)

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c $< -o $@

run-genetic: $(TARGET)
	$(TARGET) --algorithm genetic \
	    --input $(GRAPH_PATH) \
	    --output $(OUTPUT) \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME) \
	    $(if $(filter 1 true TRUE yes YES,$(SNAPSHOTS)),--save-snapshots,)
	    --population-size $(or $(POPULATION_SIZE),64) \
	    --generations $(or $(GENERATIONS),500) \
	    --mutation-rate $(or $(MUTATION_RATE),0.02)

run-welsh: $(TARGET)
	$(TARGET) --algorithm welsh_powell \
	    --input $(GRAPH_PATH) \
	    --output results/colourings/$(GRAPH_NAME)_welsh_powell.col \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME) \
	    $(if $(filter 1 true TRUE yes YES,$(SNAPSHOTS)),--save-snapshots,)

run-dsatur: $(TARGET)
	$(TARGET) --algorithm dsatur \
	    --input $(GRAPH_PATH) \
	    --output results/colourings/$(GRAPH_NAME)_dsatur.col \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME) \
	    $(if $(filter 1 true TRUE yes YES,$(SNAPSHOTS)),--save-snapshots,)

run-sa: $(TARGET)
	$(TARGET) --algorithm simulated_annealing \
	    --input $(GRAPH_PATH) \
	    --output results/colourings/$(GRAPH_NAME)_simulated_annealing.col \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME) \
	    $(if $(filter 1 true TRUE yes YES,$(SNAPSHOTS)),--save-snapshots,)

run-exact: $(TARGET)
	$(TARGET) --algorithm exact_solver \
	    --input $(GRAPH_PATH) \
	    --output results/colourings/$(GRAPH_NAME)_exact_solver.col \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME) \
	    $(if $(filter 1 true TRUE yes YES,$(SNAPSHOTS)),--save-snapshots,)

run-tabu: $(TARGET)
	$(TARGET) --algorithm tabu_search \
	    --input $(GRAPH_PATH) \
	    --output results/colourings/$(GRAPH_NAME)_tabu_search.col \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME) \
	    $(if $(filter 1 true TRUE yes YES,$(SNAPSHOTS)),--save-snapshots,)

help:
	@echo "Graph Colouring Benchmark Help"
	@echo "Targets:"
	@echo "  make all                Build benchmark runner"
	@echo "  make run-dsatur GRAPH=dimacs/myciel6.col SNAPSHOTS=1"
	@echo "  make run-welsh  GRAPH=generated/flat300_20_0.col SNAPSHOTS=1"
	@echo "  make run-genetic GRAPH=dimacs/myciel3.col POPULATION_SIZE=128 GENERATIONS=800 MUTATION_RATE=0.05 SNAPSHOTS=1"
	@echo "  make run-sa     GRAPH=dimacs/myciel3.col SNAPSHOTS=1"
	@echo "  make run-exact  GRAPH=dimacs/myciel3.col EXACT_PROGRESS_INTERVAL=2 SNAPSHOTS=1"
	@echo "  make run-tabu   GRAPH=dimacs/myciel3.col SNAPSHOTS=1"
	@echo "Variables:"
	@echo "  GRAPH=path relative to data/ (dimacs/, generated/, simple-tests/)"
	@echo "  SNAPSHOTS=1 enables per-iteration snapshot recording"
	@echo "  POPULATION_SIZE (genetic), GENERATIONS, MUTATION_RATE"
	@echo "  EXACT_PROGRESS_INTERVAL (export before run-exact or pass via env)"
	@echo "Examples:" 
	@echo "  make run-genetic GRAPH=dimacs/myciel6.col POPULATION_SIZE=200 GENERATIONS=1000 MUTATION_RATE=0.03"
	@echo "  make run-tabu GRAPH=dimacs/myciel6.col SNAPSHOTS=1"
	@echo "  EXACT_PROGRESS_INTERVAL=5 make run-exact GRAPH=dimacs/myciel6.col"

run-all-benchmarking: $(TARGET)
	python3 tools/run_all_benchmarks.py --include-generated

clean:
	rm -rf $(BUILD_DIR)


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
	$(SRC_DIR)/algorithms/exact_solver.cpp

OBJECTS := $(SOURCES:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)

.PHONY: all clean run-genetic run-welsh run-dsatur run-exact run-sa run-all-benchmarking

GRAPH ?= dimacs/myciel6.col
GRAPH_PATH := scripts/datasets/$(GRAPH)
GRAPH_FILE := $(notdir $(GRAPH))
GRAPH_NAME := $(basename $(GRAPH_FILE))
OUTPUT ?= results/raw/$(GRAPH_NAME)_genetic.col
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
	    --graph-name $(GRAPH_NAME)

run-welsh: $(TARGET)
	$(TARGET) --algorithm welsh_powell \
	    --input $(GRAPH_PATH) \
	    --output results/raw/$(GRAPH_NAME)_welsh_powell.col \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME) \
	    $(if $(filter 1 true TRUE yes YES,$(SNAPSHOTS)),--save-snapshots,)

run-dsatur: $(TARGET)
	$(TARGET) --algorithm dsatur \
	    --input $(GRAPH_PATH) \
	    --output results/raw/$(GRAPH_NAME)_dsatur.col \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME) \
	    $(if $(filter 1 true TRUE yes YES,$(SNAPSHOTS)),--save-snapshots,)

run-sa: $(TARGET)
	$(TARGET) --algorithm simulated_annealing \
	    --input $(GRAPH_PATH) \
	    --output results/raw/$(GRAPH_NAME)_simulated_annealing.col \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME)

run-exact: $(TARGET)
	$(TARGET) --algorithm exact_solver \
	    --input $(GRAPH_PATH) \
	    --output results/raw/$(GRAPH_NAME)_exact_solver.col \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME)

run-all-benchmarking: $(TARGET)
	python3 scripts/run_all_benchmarks.py --include-generated

clean:
	rm -rf $(BUILD_DIR)


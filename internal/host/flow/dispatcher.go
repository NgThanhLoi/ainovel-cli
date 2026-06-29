package flow

import (
	"fmt"
	"log/slog"
	"sync"
	"sync/atomic"

	"github.com/voocel/agentcore"
	storepkg "github.com/voocel/ainovel-cli/internal/store"
)

type Dispatcher struct {
	coordinator *agentcore.Agent
	store       *storepkg.Store
	enabled     atomic.Bool

	// 1-step writer workflow: writerStep[ch]=0 means drafter in flight, deleted when done
	writerStep map[int]int

	lastMu   sync.Mutex
	lastSent *Instruction
	repeats  int
	onRepeat func(agent, task string, n int)
}

const repeatNotifyAt = 3

func NewDispatcher(coordinator *agentcore.Agent, store *storepkg.Store) *Dispatcher {
	return &Dispatcher{coordinator: coordinator, store: store, writerStep: make(map[int]int)}
}

func (d *Dispatcher) Enable() { d.enabled.Store(true) }

func (d *Dispatcher) Attach() func() {
	return d.coordinator.Subscribe(d.handle)
}

func (d *Dispatcher) handle(ev agentcore.Event) {
	if !d.enabled.Load() {
		return
	}
	if ev.Type != agentcore.EventToolExecEnd || ev.IsError {
		return
	}
	if ev.Tool != "subagent" && ev.Tool != "reopen_book" {
		return
	}

	// 1-step workflow: after subagent completes, delete from map (done)
	if ev.Tool == "subagent" {
		for ch, sentStep := range d.writerStep {
			if sentStep == 0 {
				// Drafter just completed → auto-save text, mark done
				content := string(ev.Result)
				if content != "" && content != "(no output)" {
					if err := d.store.Drafts.SaveDraft(ch, content); err != nil {
						slog.Warn("1-step: auto-save failed", "chapter", ch, "err", err)
					} else {
						slog.Info("1-step: drafter auto-saved", "chapter", ch, "bytes", len(content))
					}
				}
				delete(d.writerStep, ch)
				slog.Info("1-step: chapter done", "chapter", ch)
			}
			break
		}
	}

	d.Dispatch()
}

func (d *Dispatcher) Dispatch() {
	state := LoadState(d.store)
	inst := Route(state)
	if inst == nil {
		return
	}

	// Intercept writer instructions for 1-step workflow: send directly to drafter
	// Coordinator handles planning and checking internally
	if inst.Agent == "writer" && inst.Chapter > 0 {
		_, exists := d.writerStep[inst.Chapter]
		if exists {
			return // already in flight
		}

		d.writerStep[inst.Chapter] = 0
		inst = &Instruction{
			Agent:   "drafter",
			Task:    fmt.Sprintf("Viết chương %d. Đây là lệnh viết chương duy nhất — hãy tự lập kế hoạch trong đầu, gọi subagent(drafter) để viết, kiểm tra và commit_chapter.", inst.Chapter),
			Reason:  fmt.Sprintf("Viết chương %d", inst.Chapter),
			Chapter: inst.Chapter,
		}
	}

	n := d.trackRepeat(inst)
	if (inst.Agent == "writer" || inst.Agent == "drafter") && inst.Chapter > 0 && d.store != nil {
		if err := d.store.Progress.ValidateChapterWork(inst.Chapter); err != nil {
			slog.Error("flow router refuses invalid dispatch", "module", "host.flow", "chapter", inst.Chapter, "err", err)
			return
		}
		if err := d.store.Progress.StartChapter(inst.Chapter); err != nil {
			slog.Warn("flow router pre-mark in-progress failed", "module", "host.flow", "chapter", inst.Chapter, "err", err)
		}
	}
	msg := formatDispatchMessage(inst, n)
	slog.Debug("flow router dispatch", "module", "host.flow", "agent", inst.Agent, "reason", inst.Reason, "repeat", n)
	d.coordinator.FollowUp(agentcore.UserMsg(msg))
}

func formatDispatchMessage(inst *Instruction, n int) string {
	msg := FormatMessage(inst)
	if n > 1 {
		msg += fmt.Sprintf("\n（注意：本指令为第 %d 次下达——上次派发后路由事实未变化。本次允许先调 novel_context 核对事实，再裁定照常执行或改派其它子代理。）", n)
	}
	return msg
}

func (d *Dispatcher) SetOnRepeat(cb func(agent, task string, n int)) {
	d.onRepeat = cb
}

func (d *Dispatcher) trackRepeat(next *Instruction) int {
	d.lastMu.Lock()
	if d.lastSent != nil && d.lastSent.Agent == next.Agent && d.lastSent.Task == next.Task {
		d.repeats++
	} else {
		cp := *next
		d.lastSent = &cp
		d.repeats = 1
	}
	n := d.repeats
	d.lastMu.Unlock()
	if n == repeatNotifyAt && d.onRepeat != nil {
		d.onRepeat(next.Agent, next.Task, n)
	}
	return n
}

func (d *Dispatcher) ResetRepeat() {
	d.lastMu.Lock()
	defer d.lastMu.Unlock()
	d.lastSent = nil
	d.repeats = 0
}
